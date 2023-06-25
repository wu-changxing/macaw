# feed/management/commands/collect.py
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from telethon.sync import TelegramClient
import os
import requests
from bs4 import BeautifulSoup
import re
from django.utils.text import slugify
from feed.models import FeedArticlePage, FeedPage
from wagtail.core.models import Site
from wagtail.core.models import Page
class Command(BaseCommand):
    help = 'Collects articles from the Telegram channel'

    def handle(self, *args, **options):
        load_dotenv()

        api_id = os.getenv('TGM_API_ID')
        api_hash = os.getenv('TGM_API_HASH')

        client = TelegramClient('my_session', api_id, api_hash)
        client.start()

        channel = client.get_entity('zhihu_bazaar')
        messages = client.get_messages('zhihu_bazaar', limit=20)

        site = Site.objects.get(is_default_site=True)

        for message in messages:
            urls = re.findall(r'(https?://\S+)', message.text.replace(')', ''))
            for url in urls:
                if 'telegra.ph' in url:
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    article_element = soup.find('article')
                    if article_element is not None:
                        h1_elements = article_element.find_all('h1')
                        p_elements = article_element.find_all('p')

                        content = "\n\n".join([elem.text for elem in p_elements])

                        slug = slugify(h1_elements[0].text) if h1_elements else slugify(content[:50])

                        # Check if the slug already exists
                        if not Page.objects.filter(slug=slug).exists():
                            article = FeedArticlePage(
                                title=h1_elements[0].text if h1_elements else 'No title',
                                slug=slug,
                                content=content,
                                live=True
                            )

                            feed_page = FeedPage.objects.first()
                            feed_page.add_child(instance=article)
                            article.save()

                            self.stdout.write(f"Article '{article.title}' has been saved.")
                        else:
                            self.stdout.write(f"Skipping article creation. Slug '{slug}' already exists.")
                    else:
                        self.stdout.write(f"Could not find the article text in the page: {url}")

        client.disconnect()
