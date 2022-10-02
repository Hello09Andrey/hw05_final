import shutil
import tempfile

from django import forms
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, User, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_none = User.objects.create_user(username='None')
        cls.user = User.objects.create_user(username='KirilMefodiy')
        cls.user_follower = User.objects.create_user(username='follower')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=Group.objects.create(
                title='Заголовок для тестовой группы',
                slug='test_slug'
            ),
            image=cls.uploaded,
        )
        cls.comments = Comment.objects.create(
            post=cls.post,
            text='Что-то там',
            author=cls.user
        )
        cls.templates_pages_names = {
            'index': {
                'url': reverse('posts:index'),
                'template': 'posts/index.html'
            },
            'group_list': {
                'url': reverse(
                    'posts:group_list', kwargs={'slug': 'test_slug'}
                ),
                'template': 'posts/group_list.html'
            },
            'profile': {
                'url': reverse(
                    'posts:profile', kwargs={'username': 'KirilMefodiy'}
                ),
                'template': 'posts/profile.html'
            },
            'post_edit': {
                'url': reverse(
                    'posts:post_edit', kwargs={'post_id': f'{cls.post.pk}'}
                ),
                'template': 'posts/create_post.html'
            },
            'post_detail': {
                'url': reverse(
                    'posts:post_detail', kwargs={'post_id': f'{cls.post.pk}'}
                ),
                'template': 'posts/post_detail.html'
            },
            'post_create': {
                'url': reverse('posts:post_create'),
                'template': 'posts/create_post.html'
            },
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client_auth_follower = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.authorized_no_follower = Client()
        self.authorized_no_follower.force_login(self.user_none)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for name, url_template in self.templates_pages_names.items():
            with self.subTest(reverse_name=url_template['url']):
                response = self.authorized_client.get(url_template['url'])
                self.assertTemplateUsed(response, url_template['template'])

    def check_post_fields(self, post):
        self.assertEqual(post.text, PostPagesTest.post.text)
        self.assertEqual(post.author, PostPagesTest.user)
        self.assertEqual(post.group, PostPagesTest.post.group)
        self.assertEqual(post.group.title, PostPagesTest.post.group.title)
        self.assertEqual(post.group.slug, PostPagesTest.post.group.slug)
        self.assertEqual(post.image, PostPagesTest.post.image)

    def test_page_show_correct_context(self):
        """
        Шаблон index, group_list, post_detail
        profile сформирован с правильным контекстом.
        """
        pages_with = [
            PostPagesTest.templates_pages_names['index']['url'],
            PostPagesTest.templates_pages_names['group_list']['url'],
            PostPagesTest.templates_pages_names['post_detail']['url'],
            PostPagesTest.templates_pages_names['profile']['url']
        ]
        for page in pages_with:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                post = response.context.get('post')
                self.check_post_fields(post)

    def test_show_correct_context(self):
        """
        Шаблон post_create(edit), post_create
        сформирован с правильным контекстом.
        """
        pages_with = [
            PostPagesTest.templates_pages_names['post_edit']['url'],
            PostPagesTest.templates_pages_names['post_create']['url'],
        ]
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for page in pages_with:
            response = self.authorized_client.get(page)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_group(self):
        """Пост попал в нужную группу."""
        response = self.authorized_client.get(
            PostPagesTest.templates_pages_names['group_list']['url']
        )
        first_object = response.context['page_obj'][0]
        text_post = PostPagesTest.post.text
        self.assertTrue(first_object.text, text_post)

    def test_post_another_group(self):
        """Пост не попал в другую группу."""
        post = Post.objects.create(
            text='Текст поста 2',
            author=self.user,
            group=Group.objects.create(
                title='Заголовок для тестовой группы 2',
                slug='test_slug2'
            ),
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug'}
            )
        )
        self.assertNotContains(response, post.text)

    def test_page_paginator(self):
        """Проверка пагинатора."""
        pages_with_paginator = [
            PostPagesTest.templates_pages_names['index']['url'],
            PostPagesTest.templates_pages_names['group_list']['url'],
            PostPagesTest.templates_pages_names['profile']['url'],
        ]
        amount_of_post = 12
        post = Post(
            author=PostPagesTest.user,
            text='Тестовый пост',
            group=PostPagesTest.post.group
        )
        post_list = [post for _ in range(amount_of_post)]
        Post.objects.bulk_create(post_list)
        page_posts_amount = [(1, 10), (2, 3)]
        for page_pag, posts in page_posts_amount:
            for page in pages_with_paginator:
                with self.subTest(page=page):
                    response = self.authorized_client.get(
                        page, {'page': page_pag}
                    )
                    self.assertEqual(len(response.context['page_obj']), posts)

    def test_authorized_add_comment(self):
        """Авторизованный может создавать комменты."""
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'комментарий'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count_comments + 1)

    def test_context_comment(self):
        """Наличие комментария с нужным context."""
        response = self.authorized_client.post(
            PostPagesTest.templates_pages_names['post_detail']['url']
        )
        post = response.context.get('post')
        self.assertEqual(
            post.comments.first().text,
            PostPagesTest.post.comments.first().text
        )
        self.assertEqual(
            post.comments.first().author,
            PostPagesTest.post.comments.first().author
        )
        self.assertEqual(
            post.comments.first().post,
            PostPagesTest.post.comments.first().post
        )

    def test_guest_not_add_comment(self):
        """
        Проверка наличия комментария с
        заданными полями (пост, автор) в БД.
        """
        self.guest_client.post(
            PostPagesTest.templates_pages_names['post_detail']['url']
        )
        self.assertTrue(Comment.objects.filter(
            text=PostPagesTest.post.comments.first().text,
            author=PostPagesTest.user,
            post=PostPagesTest.post).exists())

    def test_comment_context(self):
        """В шаблоне post_detail отображаются комментарии."""
        response = self.authorized_client.post(
            PostPagesTest.templates_pages_names['post_detail']['url']
        )
        post = response.context.get('post')
        self.assertIn(PostPagesTest.comments, post.comments.all())

    def test_cache_index(self):
        """Тест кэширования страницы index."""
        first_state = self.authorized_client.get(
            PostPagesTest.templates_pages_names['index']['url']
        )
        post_1 = Post.objects.get(pk=PostPagesTest.post.id)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(
            PostPagesTest.templates_pages_names['index']['url']
        )
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(
            PostPagesTest.templates_pages_names['index']['url']
        )
        self.assertNotEqual(first_state.content, third_state.content)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчика."""
        Follow.objects.create(
            user=PostPagesTest.user_follower,
            author=PostPagesTest.user
        )
        response = self.client_auth_follower.get(reverse('posts:follow_index'))
        post = response.context["page_obj"][0]
        self.assertEqual(post.text, PostPagesTest.post.text)
        self.assertEqual(post.author, PostPagesTest.post.author)
        self.assertEqual(post.group, PostPagesTest.post.group)

    def test_subscription_feed(self):
        """Пост не появляется, если пользователь не подписан на автора."""
        new_post = Post.objects.create(
            text='Текст поста21',
            author=self.user_none,
        )
        response = self.authorized_no_follower.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response, new_post.text)

    def test_unfollow(self):
        """При отписке, подписка на автора пропадает."""
        Follow.objects.create(
            user=PostPagesTest.user_follower,
            author=PostPagesTest.user
        )
        amount_follower = Follow.objects.filter(
            author=PostPagesTest.user
        ).count()
        self.client_auth_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={
                    'username':
                    PostPagesTest.user
                }
            )
        )
        self.assertEqual(
            Follow.objects.filter(author=PostPagesTest.user).count(),
            amount_follower - 1
        )

    def test_authorized_client_can_follow(self):
        """Авторизованный клиент может подписываться."""
        amount_follower = Follow.objects.filter(
            author=PostPagesTest.user
        ).count()
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username':
                    PostPagesTest.user
                }
            )
        )
        response = self.client_auth_follower.get(
            reverse(
                'posts:follow_index'
            )
        )
        post = response.context.get('post')
        self.assertEqual(post.text, PostPagesTest.post.text)
        self.assertEqual(post.author, PostPagesTest.user)
        self.assertEqual(
            amount_follower + 1,
            Follow.objects.filter(author=PostPagesTest.user).count()
        )
