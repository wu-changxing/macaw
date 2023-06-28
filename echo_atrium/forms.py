# echo_atrium/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, RecommendationCode, Badge
from django.core.exceptions import ObjectDoesNotExist


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    level = forms.IntegerField(required=False)  # Make level and badge optional
    badge = forms.CharField(required=False)
    recommendation_code = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'level', 'badge', 'recommendation_code']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            try:
                badge_instance = Badge.objects.get(name=self.cleaned_data.get("badge")) if self.cleaned_data.get(
                    "badge") else None
            except ObjectDoesNotExist:
                badge_instance = None
            level = self.cleaned_data.get("level") if self.cleaned_data.get("level") else 0
            user_profile = UserProfile(user=user, level=level, badge=badge_instance)
            user_profile.save()
            if self.cleaned_data.get("recommendation_code"):
                RecommendationCode.objects.create(user_profile=user_profile,
                                                  code=self.cleaned_data["recommendation_code"], use_limit=1)
        return user


class UserUpdateForm(forms.ModelForm):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    level = forms.IntegerField(required=False)
    exp = forms.IntegerField(required=False)
    credits = forms.DecimalField(required=False)
    invited_by = forms.CharField(required=False)
    badge = forms.CharField(required=False)
    recommendation_code = forms.CharField(required=False)
    use_limit = forms.IntegerField(required=False)
    times_used = forms.IntegerField(required=False)

    class Meta:
        model = User
        fields = ['user_id', 'level', 'exp', 'credits', 'invited_by', 'badge', 'recommendation_code', 'use_limit',
                  'times_used']

    def clean(self):
        cleaned_data = super().clean()
        badge = cleaned_data.get("badge")
        invited_by = cleaned_data.get("invited_by")
        if badge == "None":
            cleaned_data["badge"] = None
        elif badge:
            try:
                badge_instance = Badge.objects.get(name=badge)
            except ObjectDoesNotExist:
                # Create a new badge with level 0
                badge_instance = Badge.objects.create(name=badge, level=0)
            cleaned_data["badge"] = badge_instance

        if invited_by == "":
            cleaned_data["invited_by"] = None
        elif invited_by:
            try:
                invited_by_user = User.objects.get(username=invited_by)
                invited_by_instance = UserProfile.objects.get(user=invited_by_user)
                cleaned_data["invited_by"] = invited_by_instance  # Update here
            except User.DoesNotExist:
                self.add_error('invited_by', 'User does not exist')
            except UserProfile.DoesNotExist:
                self.add_error('invited_by', 'UserProfile does not exist')


        return cleaned_data

    def save(self, commit=True):
        user_id = self.cleaned_data.get('user_id')
        user = User.objects.get(id=user_id)
        level = self.cleaned_data.get('level')
        exp = self.cleaned_data.get('exp')
        credits = self.cleaned_data.get('credits')
        invited_by = self.cleaned_data.get('invited_by')
        badge = self.cleaned_data.get('badge')
        recommendation_code = self.cleaned_data.get('recommendation_code')
        use_limit = self.cleaned_data.get('use_limit')
        times_used = self.cleaned_data.get('times_used')

        if level is not None:
            user.userprofile.level = level
        if exp is not None:
            user.userprofile.exp = exp
        if credits is not None:
            user.userprofile.credits = credits
        if badge is not None:
            user.userprofile.badge = badge
        if invited_by is not None:
            user.userprofile.invited_by = invited_by
        user.userprofile.save()

        if recommendation_code is not None:
            user_recommend_codes = RecommendationCode.objects.filter(user_profile=user.userprofile)
            if user_recommend_codes:
                rec_code = user_recommend_codes.first()
                rec_code.code = recommendation_code
                rec_code.use_limit = use_limit or 1
                rec_code.times_used = times_used or 0
                rec_code.save()
            else:
                RecommendationCode.objects.create(
                    user_profile=user.userprofile,
                    code=recommendation_code,
                    use_limit=use_limit or 1,
                    times_used=times_used or 0,
                )

        return user
