from django.core.mail import send_mail
from django.template.loader import render_to_string
import re
from django_rq import job
from subscribe.models import Subscriber
import secrets
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
    for subscriber in subscribers:
        token = secrets.token_urlsafe()
        personalized_html_message = render_to_string(

            'email/new_blog.html',
            {
                'title': title,
                'url': f'https://aaron404.com{url_without_locale}?source=email&medium={subscriber.email}&userId={subscriber.nickname if subscriber.nickname else "anonymous"}&token={token}',
                'cover_image': cover_image_url,
                'qrcode_url': qr_code_path,
                'nickname': subscriber.nickname if subscriber.nickname else "Subscriber"  # Use nickname or a default term
            }
        )

        personalized_message = f'Hi {subscriber.nickname if subscriber.nickname else "there"}, check out our new blog post "{title}" at: https://aaron404.com{url}?source=email&medium={subscriber.email}&user={subscriber.nickname if subscriber.nickname else {subscriber.email}}'
        print(personalized_message)

        send_mail(subject, personalized_message, from_email, [subscriber.email], html_message=personalized_html_message)
