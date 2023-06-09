# /echo_atrium/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Badge(models.Model):
    level = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=0)
    exp = models.IntegerField(default=0)
    credits = models.IntegerField(default=0)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True)
    bio = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_query_name='invited_users')
    # invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - Level {self.level}'


    @property
    def is_in_debt(self):
        return self.credits < -99

class RecommendationCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    use_limit = models.IntegerField(default=1)
    times_used = models.IntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.times_used < self.use_limit
# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created and not (instance.is_staff or instance.is_superuser):
#         UserProfile.objects.create(user=instance)
#     else:
#         try:
#             instance.userprofile.save()
#         except UserProfile.DoesNotExist:
#             pass
