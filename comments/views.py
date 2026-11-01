"""Sign-to-comment: a comment is accepted only if its wallet signature recovers to the claimed address.

Anti-spam layers, cheapest first: a site-wide hourly cap (wallets are free to create), a fresh
timestamp (issued within MAX_AGE), a matching signature, a per-wallet hourly cap, and a unique
intent hash (signer + signed message) so a captured request cannot be replayed in any encoding.
"""
import hashlib
import json
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_keys.exceptions import BadSignature
from wagtail.models import Page

from blog.models import BlogPage
from flex.models import Engineer
from .models import Comment

MESSAGE = "Sign to post this comment on aaron404.com\n\nPage: {page_id}\nIssued at: {issued_at}\n\n{body}"
MAX_AGE = timedelta(minutes=10)
WALLET_LIMIT = 5
SITE_LIMIT = 30
FIELDS = ("body", "address", "signature", "issued_at")


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def parse(request):
    """The JSON payload as a dict of strings, or None if it isn't one."""
    try:
        data = json.loads(request.body)
    except ValueError:
        return None
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) for k in FIELDS):
        return None
    page_id = data.get("page_id")
    if not isinstance(page_id, int) or isinstance(page_id, bool):
        return None
    return data


def parse_time(text):
    """An aware datetime, or None for anything else (bad format or no timezone)."""
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else None


def recover(message, signature):
    try:
        return Account.recover_message(encode_defunct(text=message), signature=signature)
    except (BadSignature, ValueError):
        return None


def hour_ago():
    return timezone.now() - timedelta(hours=1)


@require_POST
def post_comment(request):
    data = parse(request)
    if data is None:
        return error("Malformed request.")
    if Comment.objects.filter(created_at__gte=hour_ago()).count() >= SITE_LIMIT:
        return error("Too many comments right now, try again later.", 429)
    body = data["body"].strip()
    if not 0 < len(body) <= 2000:
        return error("Comment must be 1–2000 characters.")
    issued_at = parse_time(data["issued_at"])
    if issued_at is None or abs(timezone.now() - issued_at) > MAX_AGE:
        return error("Signature expired, please sign again.")
    page = Page.objects.live().public().type(BlogPage, Engineer).filter(id=data.get("page_id")).first()
    if page is None:
        return error("Page not found.", 404)

    message = MESSAGE.format(page_id=page.id, issued_at=data["issued_at"], body=body)
    signer = recover(message, data["signature"])
    if signer is None or signer.lower() != data["address"].lower():
        return error("Signature does not match the wallet address.", 403)
    intent = hashlib.sha256(f"{signer.lower()}\n{message}".encode()).hexdigest()
    if Comment.objects.filter(intent=intent).exists():
        return error("This comment was already posted.", 409)
    if Comment.objects.filter(address=signer, created_at__gte=hour_ago()).count() >= WALLET_LIMIT:
        return error("Too many comments from this wallet, try again later.", 429)

    comment = Comment.objects.create(page=page, address=signer, body=body, issued_at=issued_at,
                                     signature=data["signature"], intent=intent)
    return JsonResponse({"address": comment.short_address, "body": comment.body,
                         "created_at": comment.created_at.isoformat()}, status=201)
