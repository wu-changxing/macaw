from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from subscribe.models import Subscriber


@csrf_exempt
@require_POST
def subscribe(request):
    email = request.POST.get('email')

    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    Subscriber.objects.get_or_create(email=email)

    return JsonResponse({'message': 'Successfully subscribed'})
