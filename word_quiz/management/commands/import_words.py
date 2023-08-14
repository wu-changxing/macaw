# word_quiz/management/commands/import_words.py
from django.core.management.base import BaseCommand
from .openai_utils import get_word_details
from .json_parser import process_data
from .helpers import get_category

class Command(BaseCommand):
    help = 'Import words from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file to import')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        process_data(json_file, self)
        self.stdout.write(self.style.SUCCESS(f'Successfully imported words from {json_file}'))
