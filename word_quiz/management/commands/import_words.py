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
    def get_word_details(self, word):
        response = None
        attempts = 0
        max_attempts = 3  # Maximum retries

        while attempts < max_attempts:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "system",
                         "content": "You are an advanced language model. Provide structured responses in JSON format."},
                        {"role": "user",
                         "content": f'Please provide the JSON for the English word "Change" including example sentences, chinese translation of the senteces, IPA pronunciation, root（this field for root or affix), root explanations, Chinese word usage guide, and related words(extend some words for students to learn more words in this area), level(Assign a score based on the difficulty and frequency of a word, with very common and very simple words being scored as 0, and rare words being scored as 5) .'},
                        {"role": "assistant", "content": '''
{
  "word": "change",
  "level": 1,
  "phonetics": [
    {
      "text": "/tʃeɪndʒ/"
    }
  ],
  "meanings": [
    {
      "partOfSpeech": "verb",
      "definitions": [
        {
          "definition": "使或变得不同。",
          "example": {
            "sentence": "We need to change our plans for the weekend.",
            "translation": "我们需要改变我们的周末计划。"
          }
        },
        {
          "definition": "用新的或更好的事物替换旧的事物，尤其是同类中更新或更好的事物。",
          "example": {
            "sentence": "She changed her old phone for a new one.",
            "translation": "她用新手机换掉了旧手机。"
          }
        },
        {
          "definition": "将一定金额的钱换成较小面额的硬币或纸币。",
          "example": {
            "sentence": "He changed a twenty-dollar bill for quarters.",
            "translation": "他用一张二十美元的钞票换取了零钱。"
          }
        }
      ]
    },
    {
      "partOfSpeech": "noun",
      "definitions": [
        {
          "definition": "使或变得不同的行为或过程。",
          "example": {
            "sentence": "The change in weather was sudden.",
            "translation": "天气的变化是突然的。"
          }
        },
        {
          "definition": "硬币与纸币相对的钱币。",
          "example": {
            "sentence": "I don't have any change for the vending machine.",
            "translation": "我没有零钱给自动售货机。"
          }
        },
        {
          "definition": "用较大面额的钞票换取的较小面额的零钱。",
          "example": {
            "sentence": "I need change for a ten-dollar bill.",
            "translation": "我需要找零给十美元的钞票。"
          }
        }
      ]
    }
  ],
  "root": {
    "rootWord": "cambiare",
    "explanation": "英语单词'change'来自意大利语单词'cambiare'，意为“改变”。"
  },
  "chineseGuide": "在日常生活中，我们常常需要使用 『change』 这个单词。它可以表示使事物不同，也可以用来替换旧事物为新事物，比如换手机。当你需要将一张大面额的钞票换成零钱时，你也可以使用 『change』 这个词。『Change』 这个单词的词根是 『chang-』 ，它源自拉丁语的 『changere』 ，意为 『改变』 或 『交换』。" ,
  "relatedWords": [
    {
      "word": "modify",
      "translation": "修改"
    },
    {
      "word": "transform",
      "translation": "转变"
    },
    {
      "word": "exchange",
      "translation": "交换"
    },
    {
      "word": "alter",
      "translation": "改变"
    },
    {
      "word": "shift",
      "translation": "转移"
    }
  ]
}
'''
                         },
                        {"role": "user",
                         "content": f'Now, please provide the same JSON format for the English word "{word}".'},
                    ]
                )
            # Extract the JSON details from the AI's message.
            #     self.stdout.write(self.style.SUCCESS(f'response stopped at {response["choices"][0]["finish_reason"]}'))
                details = json.loads(response['choices'][0]['message']['content'].strip())
                return details
            except Exception as e:  # Here, catch all exceptions.
                self.stdout.write(self.style.WARNING(f'JSON decoding failed. Retrying...{attempts} Error: {e}'))
                attempts += 1
        if attempts == max_attempts:
            self.stdout.write(self.style.ERROR(
                f'JSON decoding failed after {max_attempts} attempts. Please check the server response.'))


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
