from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post, User


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_author = User.objects.create_user(username='test_andrey')
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user_author
        )
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )
        cls.url_redirect = [
            (f'/posts/{cls.post.pk}/comment/', f'/posts/{cls.post.pk}/'),
            (
                f'/profile/{cls.user.username}/follow/',
                f'/profile/{cls.user.username}/'
            ),
            (
                f'/profile/{cls.user.username}/unfollow/',
                f'/profile/{cls.user.username}/'
            )
        ]
        cls.privat_url_templates = [
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.pk}/edit/', 'posts/create_post.html'),
            ('/follow/', 'posts/follow.html'),
        ]
        cls.pablic_url_templates = [
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html')
        ]
        cls.address_create = '/create/'
        cls.address_edit = f'/posts/{cls.post.pk}/edit/'
        cls.address_none = [('/unexisting_page/', 'core/404.html'), ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlTests.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostUrlTests.user_author)

    def test_urls_for_all_client(self):
        """Доступные URL без авторизации."""
        for url, template in PostUrlTests.pablic_url_templates:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        response = self.authorized_client.get(PostUrlTests.address_create)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_edit(self):
        response = self.authorized_client.get(PostUrlTests.address_edit)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_private_url(self):
        """Без авторизации приватные URL недоступны."""
        for adress, temlate in PostUrlTests.privat_url_templates:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_page_404(self):
        """
        Запрос к несуществующей странице
        и использование кастомного шаблона.
        """
        for address, template in PostUrlTests.address_none:
            with self.subTest(address=address):
                response = self.guest_client.get(PostUrlTests.address_none)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates = (
            self.pablic_url_templates + self.privat_url_templates
        )
        for address, template in url_templates:
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_template(self):
        """Адресса коментариев и подписок перенаправляются."""
        for address, template in self.url_redirect:
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertRedirects(response, template)
