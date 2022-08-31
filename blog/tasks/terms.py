from string import punctuation
import jieba
import jieba.analyse

def clean_tags(word:str):
    '''
    replacing ˜a two successive hyphens --, the tilde symbol nd any ellipsis (three or more dots ...) by a space,
    removing tags (minimal text spans between < and > inclusive) and all other characters
    :param word: str the separated words
    :return:
    '''
    import re
    word = re.sub('-{2,}',' ',word)
    word = word.replace('~', ' ') # replace ~
    word = re.sub('\.{3,}', ' ', word) # match dot
    word = re.sub('<[^>]*>', '' , word) # remove tags
    return word

def get_keywords(article):
    print('generating....')

    article = clean_tags(article)
    print('cleaned')
    jieba.analyse.set_stop_words('./blog/tasks/stopwords.txt')
    result = jieba.analyse.extract_tags(article, withWeight=True, topK=35)
    keywords = dict()
    for i in result:
        keywords[i[0]]=i[1]
    print('getted keywords')



if __name__ == '__main__':
    f = open('./t.txt')
    a = f.read()
    generate_img(article=a,path='./r.png')
