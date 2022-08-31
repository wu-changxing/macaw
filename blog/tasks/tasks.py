from celery import shared_task
from time import time
from .terms import get_keywords

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

'''Backgroud tasks'''
@shared_task()
def genetate_image(text, path):
    '''
    use generate_image.delay to call this one
    '''
    start = time()
    keywords = get_keywords(text)
    wc = WordCloud(
        # background_color='white',  # 背景颜色，根据图片背景设置，默认为黑色
        # mask = backgroup_Image, #笼罩图
        font_path='./blog/tasks/fonts/SourceHanSerif/SourceHanSerifK-Light.otf',  # 若有中文需要设置才会显示中文
        width=1920,
        height=1186,
        margin=2).generate_from_frequencies(keywords)
    # 参数 width，height，margin分别对应宽度像素，长度像素，边缘空白
    # 保存图片：默认为此代码保存的路
    wc.to_file(path)
    end = time()
    print('used',end-start)
    print('finished')


