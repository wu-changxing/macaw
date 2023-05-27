# echo_atrium/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Badge(models.Model):
    level = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)

    # add any other fields you need for badges

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=0)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True)

    # recommendation_code field is removed

    def __str__(self):
        return f'{self.user.username} - Level {self.level}'


class RecommendationCode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    use_limit = models.IntegerField(default=1)
    times_used = models.IntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.times_used < self.use_limit

# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)
#     else:
#         instance.userprofile.save()
