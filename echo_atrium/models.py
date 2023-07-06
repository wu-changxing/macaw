# /echo_atrium/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Badge(models.Model):
    level = models.IntegerField(default=0)
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
    last_exp_gain = models.DateTimeField(null=True, blank=True)  # insert one line to models.py
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_query_name='invited_users')
    # invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.exp > 20:
            self.level = 1
        elif self.exp > 200:
            self.level = 2
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} - Level {self.level}'

    @property
    def is_in_debt(self):
        return self.credits < -99


class Event(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    startDate = models.DateField()  # changed from start_date
    startTime = models.TimeField()  # changed from start_time
    endTime = models.TimeField()  # changed from end_time
    recurrence = models.CharField(max_length=100)
    recurrence_interval = models.IntegerField()
    recurrence_count = models.IntegerField()
    recurrenceByDay = models.CharField(max_length=100)  # changed from recurrence_by_day
    options = models.JSONField(default=list, blank=True)
    timeZone = models.CharField(max_length=50, default='currentBrowser')  # changed from time_zone
    location = models.CharField(max_length=100, default='Fantasy Marketplace')
    buttonStyle = models.CharField(max_length=50, default='date')  # changed from button_style
    size = models.IntegerField(default=15)
    lightMode = models.CharField(max_length=50, default='bodyScheme')  # changed from light_mode
    description = models.TextField(
        default='[p][strong]快来EAC和朋友们一起聊聊天把[/strong] 你订阅的朋友 [u]已经[/u] 上线! 🚀[/p][p]💻 [em]点击链接来访问:[/em][br]&rarr; [url]https://eac.aaron404.com/')

    def __str__(self):
        return self.name


class RecommendationCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    use_limit = models.IntegerField(default=1)
    times_used = models.IntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.times_used < self.use_limit

