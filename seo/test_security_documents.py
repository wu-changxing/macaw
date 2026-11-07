from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.models import Collection, CollectionViewRestriction


class DocumentSecurityTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        storage = self.settings(MEDIA_ROOT=directory.name, STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        })
        storage.enable()
        self.addCleanup(storage.disable)

    def test_html_upload_is_rejected_by_document_form(self):
        form_class = get_document_form(get_document_model())
        form = form_class(
            {"title": "Fictional document", "collection": Collection.get_first_root_node().pk},
            {"file": SimpleUploadedFile("fictional.html", b"<html>fictional</html>", "text/html")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("html", form.errors["file"][0])

    def test_safe_extensions_remain_uploadable(self):
        form_class = get_document_form(get_document_model())
        for extension in ("pdf", "txt", "zip", "docx", "xlsx", "pptx", "epub", "md"):
            with self.subTest(extension=extension):
                form = form_class(
                    {"title": "Fictional document", "collection": Collection.get_first_root_node().pk},
                    {"file": SimpleUploadedFile(f"fictional.{extension}", b"fictional")},
                )
                self.assertTrue(form.is_valid(), form.errors)

    def test_documents_use_the_privacy_checked_serve_view(self):
        self.assertEqual(getattr(settings, "WAGTAILDOCS_SERVE_METHOD", None), "serve_view")

    def test_document_download_is_attachment_and_restricted_collection_stays_private(self):
        collection = Collection.get_first_root_node().add_child(name="Fictional private files")
        document = get_document_model().objects.create(
            title="Fictional PDF", collection=collection,
            file=SimpleUploadedFile("fictional.pdf", b"%PDF-1.4 fictional", "application/pdf"),
        )
        response = self.client.get(document.url, secure=True)
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        CollectionViewRestriction.objects.create(collection=collection, restriction_type="login")
        private = self.client.get(document.url, secure=True)
        self.assertEqual(private.status_code, 302)
        self.assertNotIn("Content-Disposition", private)

