from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNotesCreation(TestCase):

    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'Note-1'
    NOTE_TITLE = 'Заголовок'

    @classmethod
    def setUpTestData(cls):

        cls.user = User.objects.create(username='Автор заметки')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.note = Note.objects.create(title=cls.NOTE_TITLE,
                                       text=cls.NOTE_TEXT,
                                       slug=cls.NOTE_SLUG,
                                       author=cls.user
                                       )
        # Адрес страницы с заметкой.
        cls.url = reverse('notes:detail', args=(cls.note.slug,))
        cls.add_url = reverse('notes:add', args=None)

        # Данные для POST-запроса при создании заметки.
        cls.form_data = {'title': 'Title',
                         'text': 'Text',
                         'slug': 'slug-unique',
                         }

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создавать заметки."""
        self.client.post(self.add_url, data=self.form_data)
        # Считаем количество заметок (одна - создана для тестов).
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_user_can_create_note(self):

        response = self.auth_client.post(self.add_url, data=self.form_data)
        # Проверяем редирект
        self.assertRedirects(response, reverse('notes:success', args=None))
        # Считаем количество заметок.
        notes_count = Note.objects.count()

        self.assertEqual(notes_count, 2)
        # Получаем объект комментария из базы.
        added_notes = Note.objects.all()
        added_note = added_notes[len(added_notes) - 1]
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(added_note.title, self.form_data['title'])
        self.assertEqual(added_note.slug, self.form_data['slug'])
        self.assertEqual(added_note.text, self.form_data['text'])
        self.assertEqual(added_note.author, self.user)

    def test_user_cant_use_slug_twice(self):
        """Проверка невозможности создания заметки с дублирующимся slug."""
        response = self.auth_client.post(self.add_url,
                                         data={'title': 'new title',
                                               'text': 'new text, but the same slug...',
                                               'slug': self.NOTE_SLUG
                                               })

        form = response.context['form']
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            form=form,
            field='slug',
            errors=f'{self.NOTE_SLUG}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


# class TestCommentEditDelete(TestCase):

#     COMMENT_TEXT = 'Текст комментария'
#     NEW_COMMENT_TEXT = 'Обновлённый комментарий'

#     @classmethod
#     def setUpTestData(cls):
#         # Создаём новость в БД.
#         cls.news = News.objects.create(title='Заголовок', text='Текст')
#         # Формируем адрес блока с комментариями, который понадобится для тестов.
#         news_url = reverse('news:detail', args=(cls.news.id,))  # Адрес новости.
#         cls.url_to_comments = news_url + '#comments'  # Адрес блока с комментариями.
#         # Создаём пользователя - автора комментария.
#         cls.author = User.objects.create(username='Автор комментария')
#         # Создаём клиент для пользователя-автора.
#         cls.author_client = Client()
#         # "Логиним" пользователя в клиенте.
#         cls.author_client.force_login(cls.author)
#         # Делаем всё то же самое для пользователя-читателя.
#         cls.reader = User.objects.create(username='Читатель')
#         cls.reader_client = Client()
#         cls.reader_client.force_login(cls.reader)
#         # Создаём объект комментария.
#         cls.comment = Comment.objects.create(
#             news=cls.news,
#             author=cls.author,
#             text=cls.COMMENT_TEXT
#         )
#         # URL для редактирования комментария.
#         cls.edit_url = reverse('news:edit', args=(cls.comment.id,)) 
#         # URL для удаления комментария.
#         cls.delete_url = reverse('news:delete', args=(cls.comment.id,))  
#         # Формируем данные для POST-запроса по обновлению комментария.
#         cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

#     def test_author_can_delete_comment(self):
#         comments_count = Comment.objects.count()
#         # В начале теста в БД всегда есть 1 комментарий, созданный в setUpTestData.
#         self.assertEqual(comments_count, 1)
    
#         # От имени автора комментария отправляем DELETE-запрос на удаление.
#         response = self.author_client.delete(self.delete_url)
#         # Проверяем, что редирект привёл к разделу с комментариями.
#         self.assertRedirects(response, self.url_to_comments)
#         # Заодно проверим статус-коды ответов.
#         self.assertEqual(response.status_code, HTTPStatus.FOUND)
#         # Считаем количество комментариев в системе.
#         comments_count = Comment.objects.count()
#         # Ожидаем ноль комментариев в системе.
#         self.assertEqual(comments_count, 0)

#     def test_user_cant_delete_comment_of_another_user(self):
#         # Выполняем запрос на удаление от пользователя-читателя.
#         response = self.reader_client.delete(self.delete_url)
#         # Проверяем, что вернулась 404 ошибка.
#         self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
#         # Убедимся, что комментарий по-прежнему на месте.
#         comments_count = Comment.objects.count()
#         self.assertEqual(comments_count, 1)

#     def test_author_can_edit_comment(self):
#         # Выполняем запрос на редактирование от имени автора комментария.
#         response = self.author_client.post(self.edit_url, data=self.form_data)
#         # Проверяем, что сработал редирект.
#         self.assertRedirects(response, self.url_to_comments)
#         # Обновляем объект комментария.
#         self.comment.refresh_from_db()
#         # Проверяем, что текст комментария соответствует обновленному.
#         self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

#     def test_user_cant_edit_comment_of_another_user(self):
#         # Выполняем запрос на редактирование от имени другого пользователя.
#         response = self.reader_client.post(self.edit_url, data=self.form_data)
#         # Проверяем, что вернулась 404 ошибка.
#         self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
#         # Обновляем объект комментария.
#         self.comment.refresh_from_db()
#         # Проверяем, что текст остался тем же, что и был.
#         self.assertEqual(self.comment.text, self.COMMENT_TEXT) 