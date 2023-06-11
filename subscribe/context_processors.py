# subscribe/context_processors.py
from .forms import SubscriberForm

def subscribe_form(request):
    return {'subscribe_form': SubscriberForm()}
