from django.contrib.auth.models import User
from django.db import models
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .forms import UserCreateForm
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
        context['user_profiles'] = UserProfile.objects.all()
        context['form'] = UserCreateForm()  # Add form instance to context
        return context
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = UserCreateForm()  # Add form instance to context
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('.')  # Redirect to the same page after form submission
        else:

            context = self.get_context_data(**kwargs)
            context['form'] = form  # Add form instance to context
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

