"""Regressions for backend security boundaries."""
from django.test import TestCase, override_settings

from mysite.settings import production


@override_settings(
    CORS_ALLOW_CREDENTIALS=production.CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_ALL_ORIGINS=production.CORS_ALLOW_ALL_ORIGINS,
    CORS_ALLOWED_ORIGINS=production.CORS_ALLOWED_ORIGINS,
    CORS_URLS_REGEX=getattr(production, "CORS_URLS_REGEX", r"^.*$"),
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class ProductionCORSTests(TestCase):
    def test_admin_does_not_allow_cross_origin_access(self):
        for method in (self.client.options, self.client.get):
            with self.subTest(method=method.__name__):
                response = method(
                    "/admin/login/", secure=True, HTTP_ORIGIN="https://gpt.aaron404.com",
                    HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
                )
                self.assertNotIn("Access-Control-Allow-Origin", response)
                self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_api_does_not_trust_subdomains_or_send_credentials(self):
        for origin in ("gpt", "eac", "blog"):
            with self.subTest(origin=origin):
                response = self.client.get(
                    "/api/v2/pages/", secure=True, HTTP_ORIGIN=f"https://{origin}.aaron404.com",
                )
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("Access-Control-Allow-Origin", response)
                self.assertNotIn("Access-Control-Allow-Credentials", response)

    @override_settings(CORS_ALLOWED_ORIGINS=["https://fictional-reader.example"])
    def test_even_an_allowed_origin_is_limited_to_api_without_credentials(self):
        headers = {"HTTP_ORIGIN": "https://fictional-reader.example"}
        api = self.client.get("/api/v2/pages/", secure=True, **headers)
        self.assertEqual(api["Access-Control-Allow-Origin"], headers["HTTP_ORIGIN"])
        self.assertNotIn("Access-Control-Allow-Credentials", api)
        admin = self.client.get("/admin/login/", secure=True, **headers)
        self.assertNotIn("Access-Control-Allow-Origin", admin)

