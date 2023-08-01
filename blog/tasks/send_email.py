from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
import re
import segno

@shared_task
def send_emails(title, url, cover_image_url, subscriber_emails):
    from_email = 'me@aaron404.com'
    subject = f'New blog post: {title}'
    original_url = url
    if original_url is not None:
        url_without_locale = re.sub(r'^/[a-z]{2,3}-[a-z]{2,4}', '', original_url)
    else:
        url_without_locale = "/"
    # qr = segno.make(f'http://aaron404.com{url_without_locale}')
    qr_code_path = 'static/email' + title.replace(' ', '_') + '_qr.gif'
    # qr.to_artistic(background='static/QRbackground.gif', target=qr_code_path, scale=8)
    html_message = render_to_string(
        'email/new_blog.html',
        {
            'title': title,
            'url': f'http://aaron404.com{url_without_locale}',
            'cover_image': cover_image_url,
            'qrcode_url': qr_code_path
        }
    )
    message = f'Check out our new blog post "{title}" at: http://aaron404.com{url}'

    # Send email to each subscriber
    for email in subscriber_emails:
        send_mail(subject, message, from_email, [email], html_message=html_message)
