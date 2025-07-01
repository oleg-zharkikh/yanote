from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestHomePage(TestCase):

    HOME_URL = reverse('notes:home')

    @classmethod
    def setUpTestData(cls):
        cls.user_name = User.objects.create(username='Автор заметок')
        cls.all_notes = [
            Note(
                title=f'Заметка {index}',
                text=f'Текст заметки №{index}',
                slug=f'note-{index}',
                author=cls.user_name
            )
            for index in range(10)
        ]
        Note.objects.bulk_create(cls.all_notes)

    def test_news_count(self):
        """Проверка наличия заметок на странице в порядке их создания."""
        self.client.force_login(self.user_name)
        response = self.client.get(reverse('notes:list'))
        # print('<------------CONTEXT')
        # print(response.context)
        object_list = response.context['object_list']
        notes_on_page = [note for note in object_list]
        self.assertEqual(notes_on_page, self.all_notes)
