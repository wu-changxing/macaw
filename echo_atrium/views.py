# echo_atrium/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

from rest_framework.decorators import api_view
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from .models import UserProfile, RecommendationCode,Badge
from .serializers import UserRegistrationSerializer
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

from django.contrib.auth.hashers import make_password
from .forms import UserCreateForm

def eac(request, data=None):
    # Do something with room_id if necessary
    return render(request, 'eac.html')


@login_required
def create_user(request):
    logger.info('create_user called')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            logger.info('Form is valid')
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            level = form.cleaned_data['level']
            recommendation_code = form.cleaned_data['recommendation_code']
            user = User.objects.create(username=username, password=make_password(password))
            UserProfile.objects.create(user=user, level=level, recommendation_code=recommendation_code)
            logger.info('User and profile created')
            return redirect('admin_dashboard')  # Redirect to the admin dashboard
        else:
            logger.error('Form is not valid')
            logger.error(form.errors)
    else:
        form = UserCreateForm()
    return render(request, 'create_user.html', {'form': form})


class RegisterForm(UserCreationForm):
    recommendation_code = forms.CharField(max_length=10)


@api_view(['POST'])
def api_register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return JsonResponse({'token': token.key})
    else:
        return JsonResponse(serializer.errors, status=400)



class AuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        print("this is auth token view")
        print(request.data)
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return JsonResponse({'token': token.key})


def user_login(request):
    print(request.data)
    if request.method == 'POST':
        print("start to process the login info")
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print(f"user is not none {user}")
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'token': token.key})
        else:
            return JsonResponse({"error": "Invalid username or password"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)


def user_logout(request):
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
