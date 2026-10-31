"""Sign-to-comment: a comment is accepted only if its wallet signature recovers to the claimed address.

Anti-spam comes from three checks: the signature must match, it must be fresh (issued within
MAX_AGE), and each address may post at most RATE_LIMIT comments per hour. A signature is
unique, so a captured request cannot be replayed.
"""
import json
import re
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from eth_account import Account
from eth_account.messages import encode_defunct
from wagtail.models import Page

from .models import Comment

MESSAGE = "Sign to post this comment on aaron404.com\n\nPage: {page_id}\nIssued at: {issued_at}\n\n{body}"
MAX_AGE = timedelta(minutes=10)
RATE_LIMIT = 5
SIGNATURE = re.compile(r"^0x[0-9a-fA-F]{128}(1b|1c|1B|1C)$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def signer(page_id, issued_at, body, signature):
    message = MESSAGE.format(page_id=page_id, issued_at=issued_at, body=body)
    return Account.recover_message(encode_defunct(text=message), signature=signature)


@require_POST
def post_comment(request):
    data = json.loads(request.body)
    body = data.get("body", "").strip()
    address = data.get("address", "")
    signature = data.get("signature", "")
    issued_at_text = data.get("issued_at", "")

    if not 0 < len(body) <= 2000:
        return error("Comment must be 1–2000 characters.")
    if not ADDRESS.match(address) or not SIGNATURE.match(signature):
        return error("Malformed address or signature.")
    page = Page.objects.live().filter(id=data.get("page_id")).first()
    if page is None:
        return error("Page not found.", 404)
    issued_at = datetime.fromisoformat(issued_at_text.replace("Z", "+00:00"))
    if abs(timezone.now() - issued_at) > MAX_AGE:
        return error("Signature expired, please sign again.")
    if signer(page.id, issued_at_text, body, signature).lower() != address.lower():
        return error("Signature does not match the wallet address.", 403)
    if Comment.objects.filter(signature=signature).exists():
        return error("This comment was already posted.", 409)
    recent = Comment.objects.filter(address__iexact=address, created_at__gte=timezone.now() - timedelta(hours=1))
    if recent.count() >= RATE_LIMIT:
        return error("Too many comments from this wallet, try again later.", 429)

    comment = Comment.objects.create(
        page=page, address=address, body=body, issued_at=issued_at, signature=signature
    )
    return JsonResponse({"address": comment.short_address, "body": comment.body,
                         "created_at": comment.created_at.isoformat()}, status=201)
