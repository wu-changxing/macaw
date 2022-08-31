from celery import shared_task
from time import time
from .terms import get_keywords
from celery.result import AsyncResult
from mysite import celery_app
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

'''Backgroud tasks'''
@celery_app.task
def generate_image(keywords,path):
    '''
    use generate_image.delay to call this one
    '''
    # res = AsyncResult('432890aa-4f02-437d-aaca-1999b70efe8d',app=celery_app)
    
    start = time()
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


