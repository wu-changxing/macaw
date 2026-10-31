import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from eth_account import Account
from eth_account.messages import encode_defunct
from wagtail.models import Page

from blog.models import BlogPage
from .models import Comment
from .views import MESSAGE, RATE_LIMIT


def make_post():
    root = Page.get_first_root_node()
    return root.add_child(instance=BlogPage(title="Hello", slug="hello", date=timezone.now().date(), body="<p>Hi</p>"))


class SignToCommentTests(TestCase):
    def setUp(self):
        self.page = make_post()
        self.wallet = Account.create()

    def payload(self, body="Nice post", issued_at=None, wallet=None, address=None):
        wallet = wallet or self.wallet
        issued_at = (issued_at or timezone.now()).isoformat()
        message = MESSAGE.format(page_id=self.page.id, issued_at=issued_at, body=body)
        signature = wallet.sign_message(encode_defunct(text=message)).signature.hex()
        return {"page_id": self.page.id, "body": body, "issued_at": issued_at,
                "address": address or wallet.address, "signature": "0x" + signature.removeprefix("0x")}

    def post(self, data):
        return self.client.post("/comments/", json.dumps(data), content_type="application/json")

    def test_valid_signature_is_saved(self):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.get().address, self.wallet.address)

    def test_signature_from_another_wallet_is_rejected(self):
        response = self.post(self.payload(address=Account.create().address))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Comment.objects.exists())

    def test_tampered_body_is_rejected(self):
        data = self.payload()
        data["body"] = "Buy cheap pills"
        self.assertEqual(self.post(data).status_code, 403)

    def test_stale_signature_is_rejected(self):
        response = self.post(self.payload(issued_at=timezone.now() - timedelta(hours=1)))
        self.assertEqual(response.status_code, 400)

    def test_replay_is_rejected(self):
        data = self.payload()
        self.post(data)
        self.assertEqual(self.post(data).status_code, 409)

    def test_rate_limit_per_wallet(self):
        for i in range(RATE_LIMIT):
            self.assertEqual(self.post(self.payload(body=f"comment {i}")).status_code, 201)
        self.assertEqual(self.post(self.payload(body="one too many")).status_code, 429)

    def test_body_with_format_braces_round_trips(self):
        self.assertEqual(self.post(self.payload(body="{page_id} $& {body}")).status_code, 201)

    def test_hidden_comment_not_rendered(self):
        self.post(self.payload(body="visible one"))
        self.post(self.payload(body="spam one"))
        Comment.objects.filter(body="spam one").update(is_visible=False)
        from .templatetags.comment_tags import page_comments
        bodies = [c.body for c in page_comments({"request": None}, self.page)["comments"]]
        self.assertEqual(bodies, ["visible one"])
