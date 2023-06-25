# echo_atrium/event_serializer.py
from rest_framework import serializers

from .models import UserProfile, Event
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        exclude = ['user_profile'] # Exclude user_profile from the serializer
