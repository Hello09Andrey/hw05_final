from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post, User, Comment, Follow


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='And')
        cls.user = User.objects.create_user(username='Andrey')
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug'
        )
        cls.form_data = {
            'text': 'Данные из формы',
            'group': cls.group.id
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_post(self):
        """Создаем новый пост"""
        count_posts = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=PostCreateFormTests.form_data,
            follow=True,
        )
        post = Post.objects.order_by('created').first()
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'Andrey'})
        )

        text_form = PostCreateFormTests.form_data['text']
        user_username = PostCreateFormTests.user.username
        title_group = PostCreateFormTests.group.title
        self.assertEqual(post.text, text_form)
        self.assertEqual(post.author.username, user_username)
        self.assertEqual(post.group.title, title_group)

    def test_guest_new_post(self):
        """
        Неавторизоанный не может создавать посты
        и перенапрвляется на страницу логина.
        """
        tasks_count = Post.objects.count()
        self.guest_client.post(
            reverse('posts:post_create'),
            data=PostCreateFormTests.form_data,
            follow=True,
        )
        text_form = PostCreateFormTests.form_data['text']
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertFalse(
            Post.objects.filter(
                text=text_form
            ).exists()
        )

        post = Post.objects.create(
            text='Текст поста',
            author=PostCreateFormTests.user)

        address_redirect = [
            ('/create/', '/auth/login/?next=/create/'),
            (
                f'/posts/{post.pk}/edit/',
                f'/auth/login/?next=/posts/{post.pk}/edit/'
            ),
        ]

        for adress, temlate in address_redirect:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertRedirects(response, temlate)

    def test_authorized_edit_post(self):
        """Авторизованный может редактировать"""
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=PostCreateFormTests.form_data,
            follow=True,
        )
        post = Post.objects.get(id=PostCreateFormTests.group.id)
        self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': post.id
                }
            )
        )
        modified_group = Group.objects.create(
            title='Что-то там',
            slug='test_slug2'
        )
        form_data = {
            'text': 'Измененный текст',
            'group': modified_group.id
        }
        response_edit = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': post.id
                }
            ),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=PostCreateFormTests.group.id)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(
            Post.objects.filter(
                group=modified_group.id
            ).count(), 1
        )
        self.assertEqual(
            Post.objects.filter(
                group=PostCreateFormTests.group.id
            ).count(), 0
        )

    def test_guest_new_comment(self):
        """
        Неавторизоанный не может писать коменты
        и перенапрвляется на страницу логина,
        а авторизованный может писать коменты
        """
        task_comment = Comment.objects.count()
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост1',
            group=PostCreateFormTests.group
        )

        form_data = {
            'post': post.id,
            'text': 'Данные из формы1',
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), task_comment)

        address_redirect = [
            (
                reverse('posts:add_comment', kwargs={'post_id': post.id}),
                f'/auth/login/?next=/posts/{post.pk}/comment/'
            ),
        ]

        for adress, temlate in address_redirect:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertRedirects(response, temlate)

        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), task_comment + 1)
