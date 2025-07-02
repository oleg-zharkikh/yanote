from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestHomePage(TestCase):

    HOME_URL = reverse('notes:home')

    @classmethod
    def setUpTestData(cls):
        cls.user_name = User.objects.create(username='Автор')
        cls.other_author = User.objects.create(username='Другой автор')

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

        cls.other_note = Note.objects.create(
            title='Другая заметка',
            text='Текст заметки',
            slug='note-other',
            author=cls.other_author
        )

    def test_notes_in_context(self):
        """Проверка передачи заметок на страницу со списком заметок."""
        self.client.force_login(self.user_name)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        notes_on_page = [note for note in object_list]
        self.assertEqual(notes_on_page, self.all_notes)

    def test_someone_elses_note_on_page(self):
        """Проверка отсутствия на странице заметок другого пользователя."""
        self.client.force_login(self.user_name)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        notes_on_page = set([note.slug for note in object_list])
        someone_elses_note = set((self.other_note.slug,))
        intersection = notes_on_page & someone_elses_note
        self.assertEqual(intersection, set())

    def test_authorized_client_has_form(self):
        # Проверка наличия формы при создании и редактировании заметок."""
        urls = (
            ('notes:edit', (self.other_note.slug,)),
            ('notes:add', None)
        )
        self.client.force_login(self.other_author)
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
