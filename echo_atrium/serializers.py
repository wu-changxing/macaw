# echo_atrium/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Badge, RecommendationCode


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    recommendation_code = serializers.CharField(max_length=50)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'recommendation_code']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')  # We don't need the confirmation password anymore
        recommendation_code_str = validated_data.pop('recommendation_code')

        recommendation_code = RecommendationCode.objects.filter(code=recommendation_code_str).first()
        if not recommendation_code:
            raise serializers.ValidationError("Invalid recommendation code")
        elif not recommendation_code.is_valid():
            raise serializers.ValidationError("Invalid or expired recommendation code")

        # Get the default badge
        default_badge = Badge.objects.filter(name='No badge').first()
        if not default_badge:
            default_badge = Badge.objects.create(name='No badge', level=0)

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, level=0, badge=default_badge, invited_by=recommendation_code.user_profile)
        recommendation_code.times_used += 1
        recommendation_code.save()

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = '__all__'  # This will now also include 'username'

    def get_username(self, obj):
        return obj.user.username

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'gender', 'birthday','avatar']
        read_only_fields = ['user']

    def update(self, instance, validated_data):
        instance.bio = validated_data.get('bio', instance.bio)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.birthday = validated_data.get('birthday', instance.birthday)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance
