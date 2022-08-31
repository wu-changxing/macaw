from celery import shared_task
from .gcv.wcover import generate_img

'''Backgroud tasks'''
@shared_task()
def genetate_image(text, path):
    '''
    use generate_image.delay to call this one
    '''
    generate_img(text,path)

