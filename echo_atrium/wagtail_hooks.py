# echo_atrium/wagtail_hooks.py
#views
from django.contrib.auth.models import User
from django.db import models
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .forms import UserCreateForm,UserUpdateForm
from .models import UserProfile
from wagtail.contrib.modeladmin.views import IndexView
from django.shortcuts import render, redirect

class CustomUser(User):  # Extend User model
    class Meta:
        proxy = True  # This ensures CustomUser uses the same database table as User

class CustomIndexView(IndexView):
    template_name = 'modeladmin/echo_atrium/recommendationcode/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profiles = UserProfile.objects.all()
        for user_profile in user_profiles:
            invited_users = UserProfile.objects.filter(invited_by=user_profile)
            user_profile.invited_users_list = [user.user.username for user in invited_users]
        context['user_profiles'] = user_profiles
        context['form'] = UserCreateForm()
        context['update_form'] = UserUpdateForm()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = UserCreateForm()  # Add form instance to context
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')

        if form_type == 'create_form':
            form = UserCreateForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('.')
            else:
                context = self.get_context_data(**kwargs)
                context['form'] = form  # Add form instance to context
                return render(request, self.template_name, context)
        elif form_type == 'update_form':
            form = UserUpdateForm(request.POST)
            if form.is_valid():
                user_id = form.cleaned_data.get('user_id')
                user = User.objects.get(id=user_id)
                form.instance = user
                form.save()
                return redirect('.')
            else:
                context = self.get_context_data(**kwargs)
                context['update_form'] = form  # Add form instance to context
                return render(request, self.template_name, context)


class CustomUserAdmin(ModelAdmin):
    model = CustomUser
    menu_label = 'User Admin'
    menu_icon = 'user'
    index_view_class = CustomIndexView
    list_display = ('username', 'get_level', 'get_recommendation_codes',)
    search_fields = ('username', 'userprofile__level', 'userprofile__recommendationcode__code',)

    def get_level(self, obj):
        return obj.userprofile.level
    get_level.short_description = 'Level'

    def get_recommendation_codes(self, obj):
        return ", ".join([str(rc.code) for rc in obj.userprofile.recommendationcode_set.all()])
    get_recommendation_codes.short_description = 'Recommendation Codes'

modeladmin_register(CustomUserAdmin)

