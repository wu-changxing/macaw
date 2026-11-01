from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import re
from django_rq import job
from subscribe.models import Subscriber
@job
def send_emails(title, url, cover_image_url):
    from_email = 'me@aaron404.com'
    subject = f'Blog from Aaron: {title}'
    original_url = url

    if original_url is not None:
        url_without_locale = re.sub(r'^/[a-z]{2,3}-[a-z]{2,4}', '', original_url)
    else:
        url_without_locale = "/"

    qr_code_path = 'static/email' + title.replace(' ', '_') + '_qr.gif'
    cover_image_url = f"https://aaron404.com{cover_image_url}"

    print("cover image url is ", cover_image_url)

    # Only addresses that clicked the confirmation link get the newsletter.
    subscribers = Subscriber.objects.filter(confirmed=True)

    # Send email to each subscriber
    # Tracking params identify the channel only, never the reader.
    link = f"https://aaron404.com{url_without_locale}?utm_source=email&utm_medium=newsletter"
    for subscriber in subscribers:
        nickname = subscriber.nickname or "there"
        unsubscribe_url = subscriber.link('unsubscribe')
        personalized_html_message = render_to_string(
            'email/new_blog.html',
            {
                'title': title,
                'url': link,
                'cover_image': cover_image_url,
                'qrcode_url': qr_code_path,
                'nickname': subscriber.nickname or "Subscriber",
                'unsubscribe_url': unsubscribe_url,
            }
        )
        personalized_message = (
            f'Hi {nickname}, check out our new blog post "{title}" at: {link}\n\n'
            f'Unsubscribe: {unsubscribe_url}'
        )
        send_newsletter(subject, personalized_message, personalized_html_message,
                        from_email, subscriber.email, unsubscribe_url)


def send_newsletter(subject, text, html, from_email, to_email, unsubscribe_url):
    # List-Unsubscribe headers let mail clients show their own one-click button (RFC 8058).
    headers = {
        'List-Unsubscribe': f'<{unsubscribe_url}>',
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
    }
    message = EmailMultiAlternatives(subject, text, from_email, [to_email], headers=headers)
    message.attach_alternative(html, 'text/html')
    message.send()
