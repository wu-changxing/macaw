# subscribe/views.py
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from comments.views import client_ip
from .forms import SubscriberForm
from .models import Subscriber

RESEND_INTERVAL = timedelta(minutes=10)
MAX_PENDING_SIGNUPS_PER_HOUR = 5
MAX_TOTAL_PENDING_SIGNUPS_PER_HOUR = 30


def subscribe(request):
    form = SubscriberForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request_confirmation(form.cleaned_data['email'], client_ip(request))
        # Same answer whether the address was new, pending or confirmed.
        return HttpResponseRedirect(reverse('subscribe:subscribe_success'))
    return render(request, 'subscribe_page.html', {'form': form})


def subscribe_success(request):
    return render(request, 'subscribe_success.html')


def confirm(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    subscriber.confirmed = True
    subscriber.save(update_fields=['confirmed'])
    return render(request, 'subscribe_confirmed.html')


# The token in the URL is the secret, so CSRF adds nothing here, and mail
# clients' one-click unsubscribe (RFC 8058) POSTs without a CSRF cookie.
@csrf_exempt
def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if request.method == 'POST':
        subscriber.delete()
        return render(request, 'unsubscribe_done.html')
    return render(request, 'unsubscribe_confirm.html', {'token': token})


def request_confirmation(email, ip):
    subscriber = pending_subscriber(email, ip)
    if subscriber is None or subscriber.confirmed or sent_recently(subscriber):
        return
    send_confirmation(subscriber)


@transaction.atomic
def pending_subscriber(email, ip):
    subscriber = Subscriber.objects.filter(email__iexact=email).first()
    if subscriber is None and too_many_pending_signups(ip):
        return
    if subscriber is None:
        subscriber = Subscriber.objects.create(email=email, client_ip=ip)
    return subscriber


def too_many_pending_signups(ip):
    hour_ago = timezone.now() - timedelta(hours=1)
    recent = Subscriber.objects.filter(confirmed=False, created_at__gte=hour_ago)
    return (recent.count() >= MAX_TOTAL_PENDING_SIGNUPS_PER_HOUR
            or recent.filter(client_ip=ip).count() >= MAX_PENDING_SIGNUPS_PER_HOUR)


def sent_recently(subscriber):
    sent_at = subscriber.confirmation_sent_at
    return sent_at is not None and timezone.now() - sent_at < RESEND_INTERVAL


def send_confirmation(subscriber):
    link = subscriber.link('confirm')
    message = (
        "Someone (hopefully you) asked to subscribe this address to Aaron's blog.\n\n"
        f"Confirm your subscription: {link}\n\n"
        "If it wasn't you, ignore this email and you won't hear from us again."
    )
    send_mail("Confirm your subscription to Aaron's blog", message, None, [subscriber.email])
    subscriber.confirmation_sent_at = timezone.now()
    subscriber.save(update_fields=['confirmation_sent_at'])
