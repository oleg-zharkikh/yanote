from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')

        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       slug='first-note',
                                       author=cls.author
                                       )

    def test_pages_availability(self):
        """Проверка доступности страниц."""
        users = (None, self.reader)
        urls_for_all = ('notes:home',
                        'users:login',
                        'users:logout',
                        'users:signup'
                        )
        urls_just_for_authorized = ('notes:add',
                                    'notes:list',
                                    'notes:success'
                                    )

        for user in users:
            if user:
                self.client.force_login(user)
                urls = (*urls_for_all, *urls_just_for_authorized)
            else:
                urls = urls_for_all

            for name in urls:
                with self.subTest(name=name):
                    url = reverse(name, None)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_list_edit_and_delete(self):
        """Проверка доступности заметки, ее редактирования, удаления автору."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректа для анонимных пользователей.

        Со страниц списка заметок, добавления, успешного добавления,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        login_url = reverse('users:login')
        parameterized_urls = ('notes:edit', 'notes:delete', 'notes:detail')
        not_param_urls = ('notes:add', 'notes:list', 'notes:success')

        for name in (*parameterized_urls, *not_param_urls):
            arguments = None if name in not_param_urls else (self.note.slug,)
            with self.subTest(name=name):
                url = reverse(name,
                              args=arguments
                              )
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
