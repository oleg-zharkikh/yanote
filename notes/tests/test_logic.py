from http import HTTPStatus

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestNotesCreation(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'Note-1'
    NOTE_TITLE = 'Заголовок'

    @classmethod
    def setUpTestData(cls):

        cls.user = User.objects.create(username='Автор')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.note = Note.objects.create(title=cls.NOTE_TITLE,
                                       text=cls.NOTE_TEXT,
                                       slug=cls.NOTE_SLUG,
                                       author=cls.user
                                       )

        cls.url = reverse('notes:detail', args=(cls.note.slug,))
        cls.add_url = reverse('notes:add', args=None)

        cls.form_data = {'title': 'Title',
                         'text': 'Text',
                         'slug': 'slug-unique',
                         }

    def test_anonymous_user_cant_create_note(self):
        """Проверка невозможности создания заметки анонимным пользователем."""
        self.client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_user_can_create_note(self):
        """Проверка возможности создания заметки залогиненным пользователем."""
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success', args=None))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        added_notes = Note.objects.all()
        last_added_note = added_notes[len(added_notes) - 1]
        self.assertEqual(last_added_note.title, self.form_data['title'])
        self.assertEqual(last_added_note.slug, self.form_data['slug'])
        self.assertEqual(last_added_note.text, self.form_data['text'])
        self.assertEqual(last_added_note.author, self.user)

    def test_user_cant_use_slug_twice(self):
        """Проверка невозможности создания двух заметок с одинаковым slug."""
        response = self.auth_client.post(self.add_url,
                                         data={'title': 'new title',
                                               'text': 'new text...',
                                               'slug': self.NOTE_SLUG
                                               })

        form = response.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=f'{self.NOTE_SLUG}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_generating_slug_(self):
        """Проверка автоматического заполнения slug."""
        title = 'заголовок новой заметки'
        self.auth_client.post(self.add_url,
                              data={'title': title,
                                    'text': 'заметка с автоматическим slug',
                                    'slug': ''
                                    })

        note_auto_slug = slugify(title)
        all_notes = Note.objects.all()
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        last_added_note = all_notes[notes_count - 1]
        self.assertEqual(last_added_note.slug, note_auto_slug)


class TestNoteEditDelete(TestCase):
    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновлённая заметка'
    NOTE_SLUG = 'note-test-slug'
    OTHER_NOTE_SLUG = 'other-note-test-slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )

        cls.other_author = User.objects.create(username='Другой автор')
        cls.other_client = Client()
        cls.other_client.force_login(cls.other_author)

        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_author_can_delete_note(self):
        """Проверка возможности удаления заметки автором."""
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, reverse('notes:success', None))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        note_count_after_delete = Note.objects.count()
        self.assertEqual(note_count - note_count_after_delete, 1)

    def test_user_cant_delete_note_of_another_user(self):
        """Проверка невозможности удаления чужой заметки."""
        response = self.other_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Проверка возможности редактирования своей заметки."""
        response = self.author_client.post(
            self.note_edit_url,
            data=self.form_data
        )
        self.assertRedirects(response, reverse('notes:success', None))
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        """Проверка недоступности редактирования другим пользователем."""
        response = self.other_client.post(
            self.note_edit_url,
            data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
