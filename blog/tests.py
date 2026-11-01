from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.forms import modelform_factory
from django.test import TestCase
from django.utils import timezone
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


class NotifyOnPublishTests(TestCase):
    """F10: the newsletter goes out on publish only, once, and never for restricted pages."""

    def setUp(self):
        from wagtail.models import Page
        from blog.models import BlogPage
        self.post = Page.get_first_root_node().add_child(instance=BlogPage(
            title="Notify me", slug="notify-me", date=timezone.now().date(), body="<p>x</p>", live=False))

    def flag_and(self, publish):
        from unittest import mock
        self.post.notify_subscribers = True
        revision = self.post.save_revision()
        with mock.patch("blog.models.send_emails.delay") as delay, self.captureOnCommitCallbacks(execute=True):
            if publish:
                revision.publish()
        return delay

    def test_draft_save_sends_nothing(self):
        self.flag_and(publish=False).assert_not_called()

    def test_publish_sends_once_and_clears_flag(self):
        from unittest import mock
        self.flag_and(publish=True).assert_called_once()
        self.post.refresh_from_db()
        self.assertFalse(self.post.notify_subscribers)
        self.assertFalse(self.post.latest_revision.content["notify_subscribers"])
        with mock.patch("blog.models.send_emails.delay") as again, self.captureOnCommitCallbacks(execute=True):
            self.post.save_revision().publish()
        again.assert_not_called()

    def test_restricted_page_publish_sends_nothing(self):
        from wagtail.models import PageViewRestriction
        PageViewRestriction.objects.create(page=self.post, restriction_type="password", password="x")
        self.flag_and(publish=True).assert_not_called()

    def test_admin_form_save_with_flag_sends_nothing(self):
        """The old bug: saving the edit form (e.g. a draft) with the box ticked mailed everyone."""
        form_type = modelform_factory(BlogPage, form=CoverForm, fields=['title', 'notify_subscribers', 'generate_cover'])
        form = form_type({'title': 'Draft', 'notify_subscribers': 'on'}, instance=self.post)
        self.assertTrue(form.is_valid(), form.errors)
        with patch('blog.models.send_emails.delay') as delay:
            form.save(commit=True)
        delay.assert_not_called()
