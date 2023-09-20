# echo_atrium/views.py
# Standard library imports
import logging
from datetime import timedelta
from decimal import Decimal

# Django imports
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, DecimalField
from django.db.models.functions import Least
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

# Rest Framework imports
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

# Local imports
from .forms import UserCreateForm
from .models import Badge, RecommendationCode, UserProfile, Event
from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserProfileUpdateSerializer
from .event_serializer import EventSerializer, RetriveEventSerializer

# Set up logging
logger = logging.getLogger(__name__)


def eac(request, data=None):
    # Do something with room_id if necessary
    return render(request, 'eac.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_last_checkin(request):
    user_profile = UserProfile.objects.get(user=request.user)
    last_checkin = user_profile.last_exp_gain

    # If there's no recorded last check-in, or the last check-in was more than 4 hours ago
    if not last_checkin or timezone.now() - last_checkin > timedelta(hours=4):
        return Response({"checkedIn": False})
    else:
        return Response({"checkedIn": True})


@api_view(['POST'])
def verify_token(request):
    token = request.data.get('token', None)
    if token is None:
        return JsonResponse({'valid': False})
    try:
        token_obj = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return JsonResponse({'valid': False})

    deduction = request.data.get('deduction', '0.001')
    if deduction == 0:
        return JsonResponse({'valid': True, 'message': 'No deduction'})
    profile = UserProfile.objects.get(user=token_obj.user)  # Remove select_for_update()
    updated_credits = profile.credits - Decimal(deduction)  # proposed change in credits
    if profile.credits >= Decimal('-99.0'):  # change this line
        profile.credits = updated_credits
        profile.save()
    else:
        return JsonResponse({'valid': False, 'message': 'Insufficient credits'})

    return JsonResponse({'valid': True, 'credits': profile.credits})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_invited_users(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        invited_users = UserProfile.objects.filter(invited_by=user_profile)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=404)

    data = [
        {
            'username': user.user.username,
            'date_invited': user.user.date_joined.strftime('%Y-%m-%d')  # assuming date_invited is user's join date
        }
        for user in invited_users
    ]

    return Response({'invited_users': data}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_recommend_code(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        recommendation_code = RecommendationCode.objects.filter(user_profile=user_profile).first()
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=404)
    except RecommendationCode.DoesNotExist:
        return Response({"error": "No recommendation code exists for this user."}, status=404)

    return Response({"recommendation_code": recommendation_code.code, "use_limit": recommendation_code.use_limit,
                     "times_used": recommendation_code.times_used,
                     "left_times": recommendation_code.use_limit - recommendation_code.times_used}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_update_recommend_code(request):
    specific_level = 1
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=404)

    # Check if the user is at the right level to create/update a recommendation code
    if user_profile.level < specific_level:
        return Response(
            {"error": "You need to reach level {} to create or update a recommendation code.".format(specific_level)},
            status=403)

    recommendation_code_str = request.data.get('recommendation_code', None)
    if recommendation_code_str is None:
        return Response({"error": "Recommendation code not provided."}, status=400)

    try:
        recommendation_code = RecommendationCode.objects.filter(user_profile=user_profile).first()

        if recommendation_code:
            # If the recommendation code already exists for the user, update the code
            recommendation_code.code = recommendation_code_str
            recommendation_code.save()
        else:
            # If no recommendation code exists for the user, create one
            recommendation_code = RecommendationCode.objects.create(user_profile=user_profile,
                                                                    code=recommendation_code_str)

        return Response({"success": "Recommendation code updated."}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_update_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=404)

    serializer = UserProfileUpdateSerializer(user_profile, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_avatar(request, username):
    """
    Fetches the avatar of a user by username.
    """
    try:
        user = User.objects.get(username=username)
        user_profile = UserProfile.objects.get(user=user)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    except UserProfile.DoesNotExist:
        return Response({'error': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    if user_profile.avatar:
        return Response({'avatar': request.build_absolute_uri(user_profile.avatar.url)}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'No avatar uploaded for this user.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        if request.user.is_staff or request.user.is_superuser:
            return Response({"detail": "Admin and super admin users do not have a user profile."})
        else:
            raise
    serializer = UserProfileSerializer(user_profile)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_event(request):
    user_profile = UserProfile.objects.get(user=request.user)
    events = Event.objects.filter(user_profile=user_profile)
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_all_events(request):
    paginator = PageNumberPagination()
    paginator.page_size = 20  # Define the number of events per page
    events = Event.objects.all()
    paginated_events = paginator.paginate_queryset(events, request)
    serializer = RetriveEventSerializer(paginated_events, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_user_events(request, username):
    user = get_object_or_404(User, username=username)
    events = Event.objects.filter(user_profile__user=user)
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_save_event(request):
    # Get the authenticated user's profile
    user_profile = UserProfile.objects.get(user=request.user)

    # Deserialize the incoming data
    serializer = EventSerializer(data=request.data)

    if serializer.is_valid():
        # Add the UserProfile instance to the validated data and save
        event = serializer.save(user_profile=user_profile)
        return Response({"valid": True, "id": event.id}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_update_event(request, event_id):
    """
    Update an event
    """
    # Get the authenticated user's profile
    user_profile = UserProfile.objects.get(user=request.user)

    # Retrieve the Event to update
    try:
        event = Event.objects.get(id=event_id, user_profile=user_profile)
    except Event.DoesNotExist:
        return Response({"error": "Event not found or you do not have permission to update this event."},
                        status=status.HTTP_404_NOT_FOUND)

    # Deserialize the incoming data
    serializer = EventSerializer(event, data=request.data)

    if serializer.is_valid():
        # Update the Event instance with the validated data and save
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_event(request, event_id):
    """
    Delete an event
    """
    # Get the authenticated user's profile
    user_profile = UserProfile.objects.get(user=request.user)

    # Retrieve the Event to delete
    try:
        event = Event.objects.get(id=event_id, user_profile=user_profile)
    except Event.DoesNotExist:
        return Response({"error": "Event not found or you do not have permission to delete this event."},
                        status=status.HTTP_404_NOT_FOUND)

    # Delete the Event
    event.delete()

    return Response({"message": "Event deleted successfully"}, status=status.HTTP_200_OK)


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
        print(request.data)
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            print('token created', token)
            return JsonResponse({'token': token.key})
        except ValidationError as e:
            # Here you can return whatever you want
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            # Here you can return whatever you want
            return JsonResponse({"error": "Unable to create token, please try again later"}, status=500)


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
