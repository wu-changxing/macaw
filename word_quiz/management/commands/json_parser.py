# word_quiz/management/commands/json_parser.py
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from .helpers import get_category
from word_quiz.models import Word, Sentence, Category
from django.utils.text import slugify
from feed.models import FeedPage
from .openai_utils import get_word_details
import time
def worker(data_chunk, command_instance, feed_page):
    for item in data_chunk:
        process_single_item(item, command_instance, feed_page)
def process_single_item(item, command_instance, feed_page):
    start_time = time.time()
    slug = slugify(item['name'].lower())
    existing_word = Word.objects.filter(slug=slug).first()

    file_name = item['word_type']
    category_name = get_category(file_name)
    category, created = Category.objects.get_or_create(name=category_name)
    if existing_word is None:
        # Only make API call if the word does not exist in the database
        details = get_word_details(item['name'], command_instance.stdout, command_instance.style)
        root_word = details['root']['rootWord'] if details['root'] else None
        root_explanation = details['root']['explanation'] if details['root'] else None
        related_words = details.get('relatedWords', None)

        word = Word(
            slug=slug,
            title=details['word'],
            item=details['word'],
            trans=item['trans'],
            usphone=item.get('usphone', 'N/A'),
            ukphone=item.get('ukphone', 'N/A'),
            ipa=details['phonetics'][0]['text'],
            word_type=file_name,
            root=root_word,
            root_explanation=root_explanation,
            chinese_guide=details['chineseGuide'],
            related_words=related_words,
            language='en',
            meanings=details['meanings'],
            level=details['level'],
        )
        feed_page.add_child(instance=word)
        word.categories.add(category)

        # create Sentence objects for each meaning
        for meaning in details['meanings']:
            for definition in meaning['definitions']:
                sentence_text = definition['example']['sentence']
                translation_text = definition['example'].get('translation', None)
                sentence = Sentence(
                    sentence=sentence_text,
                    translation=translation_text
                )
                sentence.save()
                word.sentences.add(sentence)  # associate the Sentence with the Word

        word.save()
        elapsed_time = time.time() - start_time
        command_instance.stdout.write(
            command_instance.style.SUCCESS(
                f'Successfully imported -> {item["name"]} | {details["level"]} in {elapsed_time:.2f} seconds from {file_name}'))
    else:
        if category not in existing_word.categories.all():
            existing_word.categories.add(category)
            existing_word.save()
            command_instance.stdout.write(
                command_instance.style.SUCCESS(f'Added category "{category_name}" to -> {item["name"]}'))
        else:
            command_instance.stdout.write(command_instance.style.WARNING(
                f'Word "{item["name"]}" already has the category "{category_name}". Skipped.'))

def process_data(json_file, command_instance):
    with open(json_file, 'r') as file:
        data = json.load(file)

    file_name = os.path.basename(json_file).split('.')[0]
    feed_page = FeedPage.objects.filter(title="dicts").first()

    # Add a word_type to each data item
    for item in data:
        item['word_type'] = file_name

    max_threads = 10  # adjust the maximum number of threads
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_single_item, item, command_instance, feed_page) for item in data]

        # ensure all threads are complete
        for future in futures:
            future.result()
