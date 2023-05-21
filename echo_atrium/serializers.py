# echo_atrium/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Badge, RecommendationCode
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    recommendation_code = serializers.CharField(max_length=10)

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

        try:
            recommendation_code = RecommendationCode.objects.get(code=recommendation_code_str)
            if recommendation_code.is_valid():
                # Get the default badge
                default_badge = Badge.objects.filter(name='No badge').first()
                user = User.objects.create(**validated_data)
                user.set_password(password)
                user.save()
                user_profile = UserProfile.objects.create(user=user, level=0, badge=default_badge)
                recommendation_code.user_profile = user_profile  # Link the user profile to the recommendation code
                recommendation_code.times_used += 1
                recommendation_code.save()
                return user
            else:
                raise serializers.ValidationError("Invalid or expired recommendation code")
        except RecommendationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid recommendation code")
