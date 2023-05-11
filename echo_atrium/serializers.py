# echo_atrium/models.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, RoomParticipant, RecommendationCode

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'created_at']

class RoomParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = RoomParticipant
        fields = ['user', 'room', 'joined_at']

class RecommendationCodeSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = RecommendationCode
        fields = ['code', 'user', 'created_at']
