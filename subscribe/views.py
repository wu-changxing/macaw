
# subscribe/views.py

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import SubscriberForm
from django.shortcuts import redirect

def subscribe(request):
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('subscribe:subscribe_success'))
    else:
        form = SubscriberForm()

    return render(request, 'subscribe_page.html', {'form': form})

def subscribe_success(request):
    return render(request, 'templates/subscribe_success.html')
