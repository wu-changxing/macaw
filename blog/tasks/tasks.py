from time import time
from io import BytesIO
import jieba
import jieba.analyse
import os
import re
from wordcloud import WordCloud
from django_rq import job
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

cwd = os.getcwd()

# Construct the path to your stopwords.txt file
STOPWORDS_PATH = os.path.join(cwd, 'blog/tasks/stopwords.txt')

def clean_tags(word: str):
    '''
    replacing ˜a two successive hyphens --, the tilde symbol and any ellipsis (three or more dots ...) by a space,
    removing tags (minimal text spans between < and > inclusive) and all other characters
    :param word: str the separated words
    :return:
    '''
    word = re.sub('-{2,}', ' ', word)
    word = word.replace('~', ' ')  # replace ~
    word = word.replace('text', ' ')  # replace text
    word = word.replace('button', ' ')  # replace button
    word = word.replace('blocks', ' ')  # replace blocks
    word = re.sub('\.{3,}', ' ', word)  # match dot
    word = re.sub('<[^>]*>', '', word)  # remove tags
    return word

@job
def generate_keywords_and_image(article, filename):
    '''Generate a PNG and save it under a storage-relative cover filename.'''

    # Keyword extraction
    print('generating keywords...')
    article = clean_tags(article)
    jieba.analyse.set_stop_words(stop_words_path=STOPWORDS_PATH)
    result = jieba.analyse.extract_tags(article, withWeight=True, topK=35)
    keywords = dict()
    for i in result:
        keywords[i[0]] = i[1]
    print('keywords generated.')

    # Generate word cloud
    print('generating word cloud...')
    start = time()
    wc = WordCloud(
        background_color='white',
        font_path='./blog/tasks/fonts/SourceHanSerif/SourceHanSerifK-Light.otf',
        width=1920,
        height=1186,
        margin=2).generate_from_frequencies(keywords)

    image = BytesIO()
    wc.to_image().save(image, format='PNG')
    saved_name = default_storage.save(filename, ContentFile(image.getvalue()))
    end = time()
    print(f'word cloud generation took {end - start} seconds.')
    print('word cloud generation finished.')
    return saved_name
