# echo_atrium/event_serializer.py
from rest_framework import serializers

from django.contrib.auth.models import User
from .models import UserProfile, Event, Badge


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        exclude = ['user_profile'] # Exclude user_profile from the serializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('level', 'name')

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('user', 'level', 'exp', 'avatar', 'badge')


class RetriveEventSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
