from wagtail import hooks
from .tasks import genetate_image

@hooks.register('after_publish_page')
def save_image(request,page):
    body = page.body
    title = request.POST['title']
    path ='media/' + title + '.png'
    genetate_image.delay(body,path)
