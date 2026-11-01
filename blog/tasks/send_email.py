from django.core.mail import send_mail
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

    # Fetch all subscribers from the database
    subscribers = Subscriber.objects.all()

    # Send email to each subscriber
    # Tracking params identify the channel only, never the reader.
    link = f"https://aaron404.com{url_without_locale}?utm_source=email&utm_medium=newsletter"
    for subscriber in subscribers:
        nickname = subscriber.nickname or "there"
        personalized_html_message = render_to_string(
            'email/new_blog.html',
            {
                'title': title,
                'url': link,
                'cover_image': cover_image_url,
                'qrcode_url': qr_code_path,
                'nickname': subscriber.nickname or "Subscriber",
            }
        )
        personalized_message = f'Hi {nickname}, check out our new blog post "{title}" at: {link}'
        send_mail(subject, personalized_message, from_email, [subscriber.email], html_message=personalized_html_message)
