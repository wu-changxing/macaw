# blog/tasks/terms.py
from string import punctuation
import jieba
import jieba.analyse
import os
import re
from django_rq import job

cwd = os.getcwd()

# Construct the path to your stopwords.txt file
STOPWORDS_PATH = os.path.join(cwd, 'blog/tasks/stopwords.txt')

def clean_tags(word:str):
    '''
    replacing ˜a two successive hyphens --, the tilde symbol and any ellipsis (three or more dots ...) by a space,
    removing tags (minimal text spans between < and > inclusive) and all other characters
    :param word: str the separated words
    :return:
    '''
    word = re.sub('-{2,}',' ',word)
    word = word.replace('~', ' ') # replace ~
    word = word.replace('text', ' ') # replace ~
    word = word.replace('button', ' ') # replace ~
    word = word.replace('blocks', ' ') # replace ~
    word = re.sub('\.{3,}', ' ', word) # match dot
    word = re.sub('<[^>]*>', '' , word) # remove tags
    return word

@job
def get_keywords(article):
    print('generating....')

    article = clean_tags(article)
    print('cleaned')
    jieba.analyse.set_stop_words(stop_words_path=STOPWORDS_PATH)
    result = jieba.analyse.extract_tags(article, withWeight=True, topK=35)
    keywords = dict()
    for i in result:
        keywords[i[0]]=i[1]
    print('getted keywords')

    return keywords

if __name__ == '__main__':
    f = open('./t.txt')
    a = f.read()
