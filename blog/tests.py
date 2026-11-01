from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.forms import modelform_factory
from django.test import TestCase
from PIL import Image

from flex.models import CoverForm as FlexCoverForm, Engineer
from .models import BlogPage, CoverForm
from .tasks.tasks import generate_keywords_and_image


class GeneratedCoverTests(TestCase):
    def assert_cover_stays_in_media(self, model, form_class, **content):
        page = model(title='Original title', date=date(2026, 1, 1), **content)
        form_type = modelform_factory(model, form=form_class, fields=['title', 'generate_cover'])
        form = form_type({'title': '../mysite/static/cover', 'generate_cover': 'on'}, instance=page)
        self.assertTrue(form.is_valid(), form.errors)
        with patch.object(generate_keywords_and_image, 'delay') as enqueue:
            page = form.save(commit=False)
        article, filename = enqueue.call_args.args
        self.assertRegex(filename, r'^covers/[0-9a-f]{32}\.png$')
        self.assertEqual(page.cover_image.name, filename)
        self.assertFalse(page.generate_cover)

        with TemporaryDirectory() as directory:
            media_root = Path(directory).resolve() / 'media'
            outside_file = Path(directory) / 'mysite/static/cover.png'
            outside_file.parent.mkdir(parents=True)
            outside_file.write_bytes(b'existing file')
            with self.settings(MEDIA_ROOT=str(media_root)):
                saved_name = generate_keywords_and_image(article, filename)
                self.assertEqual(saved_name, filename)
                destination = Path(page.cover_image.path).resolve()
                self.assertEqual(destination.parent, media_root / 'covers')
                self.assertTrue(destination.is_file())
                with Image.open(destination) as image:
                    self.assertEqual(image.format, 'PNG')
                self.assertEqual(page.cover_image.url, f'/media/{filename}')
            self.assertEqual(outside_file.read_bytes(), b'existing file')
            self.assertEqual(list(media_root.rglob('*.png')), [destination])

    def test_blog_title_cannot_escape_media(self):
        self.assert_cover_stays_in_media(
            BlogPage, CoverForm, body='<p>Translation alignment storage safety website article</p>')

    def test_flex_title_cannot_escape_media(self):
        self.assert_cover_stays_in_media(
            Engineer, FlexCoverForm,
            content=[{'type': 'full_richtext',
                      'value': '<p>Translation alignment storage safety website article</p>'}])
