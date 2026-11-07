from django.test import TestCase, override_settings


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class IPv6LoginTests(TestCase):
    def test_axes_shares_failures_within_subnet_on_both_logins(self):
        from django.contrib.auth import get_user_model
        from axes.models import AccessAttempt

        get_user_model().objects.create_superuser(
            "fictional-editor", "fictional-editor@example.com", "correct-password",
        )
        for index, path in enumerate(("/admin/login/", "/django-admin/login/")):
            with self.subTest(path=path):
                subnet = f"2001:db8:{index}"
                for _ in range(5):
                    self.client.post(path, {"username": "fictional-editor", "password": "wrong"},
                                     HTTP_CF_CONNECTING_IP=f"{subnet}::1")
                blocked = self.client.post(
                    path, {"username": "fictional-editor", "password": "correct-password"},
                    HTTP_CF_CONNECTING_IP=f"{subnet}::abcd",
                )
                self.assertEqual(blocked.status_code, 429)
                self.assertEqual(AccessAttempt.objects.get(ip_address=f"{subnet}::").failures_since_start, 5)
                allowed = self.client.post(
                    path, {"username": "fictional-editor", "password": "correct-password"},
                    HTTP_CF_CONNECTING_IP=f"{subnet}:1::1",
                )
                self.assertEqual(allowed.status_code, 302)
                self.client.logout()
