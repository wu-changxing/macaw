import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.utils.text import slugify
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
from feed.models import BookPage, FeedPage
from wagtail.models import Site
from wagtail.documents.models import Document
import re

class Command(BaseCommand):
    help = 'Collects books from the Telegram channel'

    def add_arguments(self, parser):
        # Named (optional) argument
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of messages to collect. Default is 20.',
        )

    def handle(self, *args, **options):
        load_dotenv()

        api_id = os.getenv('TGM_API_ID')
        api_hash = os.getenv('TGM_API_HASH')

        client = TelegramClient('my_session', api_id, api_hash)
        client.start()

        channel = client.get_entity('MothLib')
        messages = client.get_messages('MothLib', limit=options['limit'])  # Use the passed limit

        site = Site.objects.get(is_default_site=True)
        feed_page = FeedPage.objects.filter(title="书籍推荐").first()

        if feed_page is None:
            self.stdout.write("The '书籍推荐' page does not exist. Exiting.")
            return

        for message in messages:
            if message.media and hasattr(message.media, 'document'):
                for attribute in message.media.document.attributes:
                    if isinstance(attribute, DocumentAttributeFilename):
                        if attribute.file_name.lower().endswith(('.mobi', '.epub', '.pdf')):
                            # Extract title from the message using regex
                            title_search = re.search(r'《(.*?)》', message.text)
                            if title_search is None:
                                continue  # If no title, skip this message

                            title = title_search.group(1)
                            slug = slugify(title)

                            # Use the message text as content
                            content = message.text

                            # The introduction is a brief part of the content
                            introduction = content[:250]

                            # Check if a book page with the same title already exists
                            existing_book_page = BookPage.objects.filter(title=title).first()
                            if existing_book_page is not None:
                                self.stdout.write(f"Skipping book creation. Title '{title}' already exists.")
                                continue

                            # Check the file size without downloading it
                            file_size = message.media.document.size
                            if file_size > 50 * 1024 * 1024:  # 50MB in bytes
                                print()
                                self.stdout.write(f"Skipping book{title} creation. File size exceeds 50MB: {file_size} bytes.")
                                continue

                            # Download the book after ensuring title and content are available
                            print("Downloading book: {}, file size is{}".format(title, file_size))
                            file_path = client.download_media(message=message, file='media/books/{}'.format(attribute.file_name))

                            # Read the file content into memory
                            with open(file_path, 'rb') as file:
                                file_content = file.read()

                            # Create a new Document instance for the downloaded file
                            book_file = ContentFile(file_content)
                            book_file.name = attribute.file_name
                            book_file.seek(0)

                            book_document = Document.objects.create(
                                title=title,
                                file=book_file
                            )

                            book_page = BookPage(
                                title=title,
                                slug=slug,
                                introduction=introduction,
                                content=content,
                                attachment=book_document,
                                live=True
                            )

                            feed_page.add_child(instance=book_page)
                            book_page.save()

                            self.stdout.write(f"Book '{book_page.title}' has been saved.")

        client.disconnect()
