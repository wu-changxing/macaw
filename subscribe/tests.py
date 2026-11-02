from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from blog.tasks.send_email import send_emails
from subscribe import views
from subscribe.models import Subscriber


def post_subscribe(client, email):
    return client.post(reverse('subscribe:new'), {'email': email})


def confirm_link_in(message):
    return next(word for word in message.body.split() if '/subscribe/confirm/' in word)


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class SubscribeFlowTests(TestCase):
    def test_new_signup_is_pending_until_confirmed(self):
        post_subscribe(self.client, '  Reader@Example.com ')
        subscriber = Subscriber.objects.get()
        self.assertEqual(subscriber.email, 'reader@example.com')
        self.assertFalse(subscriber.confirmed)

    def test_signup_sends_one_confirmation_email_that_confirms(self):
        post_subscribe(self.client, 'reader@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['reader@example.com'])
        path = confirm_link_in(mail.outbox[0]).split('aaron404.com', 1)[1]
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Subscriber.objects.get().confirmed)

    def test_invalid_tokens_404(self):
        self.assertEqual(self.client.get(reverse('subscribe:confirm', args=['nope'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('subscribe:unsubscribe', args=['nope'])).status_code, 404)
        self.assertEqual(self.client.post(reverse('subscribe:unsubscribe', args=['nope'])).status_code, 404)

    def test_confirmation_is_not_resent_within_ten_minutes(self):
        post_subscribe(self.client, 'reader@example.com')
        post_subscribe(self.client, 'reader@example.com')
        self.assertEqual(len(mail.outbox), 1)
        Subscriber.objects.update(confirmation_sent_at=timezone.now() - timedelta(minutes=11))
        post_subscribe(self.client, 'READER@example.com')
        self.assertEqual(len(mail.outbox), 2)

    def test_response_does_not_reveal_membership(self):
        Subscriber.objects.create(email='member@example.com', confirmed=True)
        known = post_subscribe(self.client, 'member@example.com')
        unknown = post_subscribe(self.client, 'stranger@example.com')
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known['Location'], unknown['Location'])
        # A confirmed member is not mailed again.
        self.assertEqual([m.to for m in mail.outbox], [['stranger@example.com']])

    def test_hourly_cap_on_pending_signups(self):
        with patch.object(views, 'MAX_PENDING_SIGNUPS_PER_HOUR', 2):
            for n in range(3):
                post_subscribe(self.client, f'reader{n}@example.com')
        self.assertEqual(Subscriber.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_unsubscribe_page_asks_then_post_removes(self):
        subscriber = Subscriber.objects.create(email='reader@example.com', confirmed=True)
        url = reverse('subscribe:unsubscribe', args=[subscriber.token])
        self.assertContains(self.client.get(url), 'Unsubscribe')
        self.assertTrue(Subscriber.objects.exists())
        self.client.post(url)
        self.assertFalse(Subscriber.objects.exists())


    def test_pending_cap_is_per_ip_with_cloudflare_precedence(self):
        headers = {"HTTP_CF_CONNECTING_IP": "192.0.2.1", "HTTP_X_FORWARDED_FOR": "192.0.2.99"}
        for i in range(6):
            self.client.post(reverse("subscribe:new"), {"email": f"reader{i}@example.com"}, **headers)
        self.assertEqual(Subscriber.objects.count(), 5)
        headers["HTTP_CF_CONNECTING_IP"] = "192.0.2.2"
        self.client.post(reverse("subscribe:new"), {"email": "other@example.com"}, **headers)
        self.assertEqual(Subscriber.objects.count(), 6)


class NewsletterTests(TestCase):
    def send(self):
        send_emails('Hello', '/hello/', '/media/cover.png')

    def test_only_confirmed_subscribers_get_the_newsletter_with_unsubscribe_link(self):
        confirmed = Subscriber.objects.create(email='confirmed@example.com', confirmed=True)
        Subscriber.objects.create(email='pending@example.com')
        self.send()
        self.assertEqual([m.to for m in mail.outbox], [['confirmed@example.com']])
        message = mail.outbox[0]
        link = confirmed.link('unsubscribe')
        self.assertIn(link, message.body)
        self.assertIn(link, message.alternatives[0][0])
        self.assertEqual(message.extra_headers['List-Unsubscribe'], f'<{link}>')

    def test_unsubscribed_reader_gets_no_more_mail(self):
        subscriber = Subscriber.objects.create(email='reader@example.com', confirmed=True)
        self.client.post(reverse('subscribe:unsubscribe', args=[subscriber.token]))
        self.send()
        self.assertEqual(len(mail.outbox), 0)


class GrandfatherMigrationTests(TransactionTestCase):
    def test_existing_rows_become_confirmed_with_distinct_tokens(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('subscribe', '0003_subscriber_nickname')])
        old = executor.loader.project_state(('subscribe', '0003_subscriber_nickname')).apps
        OldSubscriber = old.get_model('subscribe', 'Subscriber')
        OldSubscriber.objects.create(email='one@example.com')
        OldSubscriber.objects.create(email='two@example.com')

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([('subscribe', '0004_subscriber_double_optin')])

        migrated = executor.loader.project_state(("subscribe", "0004_subscriber_double_optin")).apps
        rows = migrated.get_model("subscribe", "Subscriber").objects.all()
        self.assertTrue(all(row.confirmed for row in rows))
        self.assertEqual(len({row.token for row in rows}), 2)
        executor.migrate(executor.loader.graph.leaf_nodes())
