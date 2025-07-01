from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор Первый')
        cls.reader = User.objects.create(username='Автор Второй')

        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       slug='first-note',
                                       author=cls.author
                                       )

    def test_pages_availability(self):
        """Доступность базовых страниц незарегистрированному пользователю."""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_edit_and_delete(self):
        """Доступность функций редактирования и удаления заметок."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Редирект для анонимных пользователей."""
        login_url = reverse('users:login')
        url_create_note = 'notes:add'

        for name in (url_create_note, 'notes:edit', 'notes:delete'):
            arguments = None if name == url_create_note else (self.note.slug,)
            with self.subTest(name=name):
                url = reverse(name,
                              args=arguments
                              )
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
