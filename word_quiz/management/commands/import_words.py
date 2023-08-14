import os
import json
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from word_quiz.models import Word, Sentence
import openai
from django.utils.text import slugify
from feed.models import FeedPage

# Load environment variables
load_dotenv()

# Get OpenAI API key from .env
openai.api_key = os.getenv('OPENAI_API_KEY')


class Command(BaseCommand):
    help = 'Import words from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file to import')

    def get_catagory(self, file_name):
        if 'IELTS' in file_name:
            catagory = 'IELTS'
        elif 'TOEFL' in file_name:
            catagory = 'TOEFL'
        elif 'GRE' in file_name:
            catagory = 'GRE'
        elif 'SAT' in file_name:
            catagory = 'SAT'
        elif 'GMAT' in file_name:
            catagory = 'GMAT'
        elif 'CET4' in file_name:
            catagory = 'CET4'
        elif 'CET6' in file_name:
            catagory = 'CET6'
        elif 'KET' in file_name:
            catagory = 'KET'
        elif 'PET' in file_name:
            catagory = 'PET'
        elif 'FCE' in file_name:
            catagory = 'FCE'
        elif 'PTE' in file_name:
            catagory = 'PTE'
        return catagory


    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        with open(json_file, 'r') as file:
            data = json.load(file)

        file_name = os.path.basename(json_file).split('.')[0]
        feed_page = FeedPage.objects.filter(title="dicts").first()

        for item in data:
            slug = slugify(item['name'].lower())
            existing_word = Word.objects.filter(slug=slug).first()

            if existing_word is None:
                # Only make API call if the word does not exist in the database
                details = self.get_word_details(item['name'])
                root_word = details['root']['rootWord'] if details['root'] else None
                root_explanation = details['root']['explanation'] if details['root'] else None
                if 'relatedWords' in details:
                    related_words = details['relatedWords']
                else:
                    related_words = None
                catagory = self.get_catagory(file_name)
                word = Word(
                    slug=slug,
                    title=details['word'],
                    item=details['word'],
                    trans=item['trans'],
                    usphone=item['usphone'] if 'usphone' in item else 'N/A',
                    ukphone=item['ukphone'] if 'ukphone' in item else 'N/A',
                    ipa=details['phonetics'][0]['text'],
                    word_type=file_name,
                    root=root_word,
                    root_explanation=root_explanation,
                    chinese_guide=details['chineseGuide'],
                    related_words=related_words,
                    language='en',
                    meanings=details['meanings'],
                    level=details['level'],
                    catagory=catagory,
                )
                feed_page.add_child(instance=word)

                # create Sentence objects for each meaning
                for meaning in details['meanings']:
                    for definition in meaning['definitions']:
                        sentence_text = definition['example']['sentence']
                        translation_text = definition['example'].get('translation',
                                                                     None)  # Provide a default value of None when 'translation' is not present
                        sentence = Sentence(
                            sentence=sentence_text,
                            translation=translation_text
                        )
                        sentence.save()
                        word.sentences.add(sentence)  # associate the Sentence with the Word

                word.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully imported -> {item["name"]} {details["level"]} from {file_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Word "{item}" already exists. Skipped.'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported words from {json_file}'))
