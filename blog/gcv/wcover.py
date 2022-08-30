import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import jieba
import jieba.analyse

from string import punctuation
import asyncio

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


def generate_img(article:str,path:str):
    print('generating....')
    article = clean_tags(article)
    print('cleaned')
    jieba.analyse.set_stop_words('./blog/gcv/stopwords.txt')
    result = jieba.analyse.extract_tags(article, withWeight=True, topK=35)
    keywords = dict()
    for i in result:
      keywords[i[0]]=i[1]

    wc = WordCloud(
        background_color='white',  # 背景颜色，根据图片背景设置，默认为黑色
        # mask = backgroup_Image, #笼罩图
        font_path='./blog/gcv/fonts/SourceHanSerif/SourceHanSerifK-Light.otf',  # 若有中文需要设置才会显示中文
        width=1920,
        height=1186,
        margin=2)
    wc.generate_from_frequencies(keywords)
    # 参数 width，height，margin分别对应宽度像素，长度像素，边缘空白
    # 保存图片：默认为此代码保存的路
    wc.to_file(path)
    print('finished')

if __name__ == '__main__':
    f = open('./t.txt')
    a = f.read()
    generate_img(article=a,path='./r.png')
