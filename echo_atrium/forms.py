# echo_atrium/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, RecommendationCode,Badge
from django.core.exceptions import ObjectDoesNotExist

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    level = forms.IntegerField()
    badge = forms.CharField()  # Change this to a ModelChoiceField if you have predefined badges
    recommendation_code = forms.CharField()

    class Meta:
        model = User
        fields = ['username', 'password', 'level', 'badge', 'recommendation_code']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            try:
                badge_instance = Badge.objects.get(name=self.cleaned_data["badge"])  # Fetch the Badge instance
            except ObjectDoesNotExist:
                # Handle the case when the badge does not exist in the database
                # You could create a new Badge instance here, or handle the error in another way
                badge_instance = None
            user_profile = UserProfile(user=user, level=self.cleaned_data["level"], badge=badge_instance)  # Assign the Badge instance
            user_profile.save()
            RecommendationCode.objects.create(user_profile=user_profile, code=self.cleaned_data["recommendation_code"], use_limit=1)
        return user

