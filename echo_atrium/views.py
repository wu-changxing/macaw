# echo_atrium/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from .models import Room, RoomParticipant, RecommendationCode
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .serializers import RoomSerializer, RoomParticipantSerializer, RecommendationCodeSerializer
from rest_framework.decorators import api_view
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from .models import RecommendationCode, Room, RoomParticipant
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework import status


@require_POST
def add_recommendation_code(request):
    code = request.POST['code']
    username = request.POST['user']
    user = None

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # Handle the case when the provided username does not exist
        print('User does not exist')
        pass
    if user is None:
        # Create a new user
        user = User.objects.create(username=username, password='shortestpasswordever')

    # Check if the code already exists
    if RecommendationCode.objects.filter(code=code).exists():
        messages.error(request, 'A recommendation code with this code already exists.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    RecommendationCode.objects.create(code=code, user=user)
    return redirect(request.META.get('HTTP_REFERER', '/'))


class RegisterForm(UserCreationForm):
    recommendation_code = forms.CharField(max_length=10)
@api_view(['POST'])
def api_register(request):
    print(request.data)
    serializer = UserCreationForm(data=request.data)
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
        if form.is_valid():
            recommendation_code = form.cleaned_data['recommendation_code']
            try:
                RecommendationCode.objects.get(code=recommendation_code)
                user = form.save()
                # Generate a new recommendation code for the new user
                RecommendationCode.objects.create(user=user)
                # Log the user in
                login(request, user)
                return redirect('room_list')
            except RecommendationCode.DoesNotExist:
                form.add_error('recommendation_code', 'Invalid recommendation code')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


