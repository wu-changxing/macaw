import uuid
import datetime
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

@database_sync_to_async
def get_token(token_str):
    from rest_framework.authtoken.models import Token
    try:
        return Token.objects.get(key=token_str)
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def update_user_exp(token_str, exp):
    from rest_framework.authtoken.models import Token
    token = Token.objects.get(key=token_str)
    user = token.user
    now = timezone.now()  # Now 'now' is timezone-aware

    try:
        user_profile = user.userprofile
        if not user_profile.last_exp_gain or now - user_profile.last_exp_gain >= datetime.timedelta(hours=4):
            user_profile.exp += exp
            user_profile.last_exp_gain = now
            user_profile.save()
        return user_profile.exp
    except ObjectDoesNotExist:
        # Handle case where user does not have a UserProfile
        pass


@database_sync_to_async
def check_user_status(token_str):
    print("Checking status")
    from rest_framework.authtoken.models import Token
    token = Token.objects.get(key=token_str)
    user = token.user
    now = timezone.now()  # Now 'now' is timezone-aware

    try:
        user_profile = user.userprofile

        if not user_profile.last_exp_gain:
            return (True, "You can check again immediately.")
        elif now - user_profile.last_exp_gain >= datetime.timedelta(hours=4):
            difference = now - user_profile.last_exp_gain
            hours, remainder = divmod(difference.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return (True, "You can check again immediately.")
        else:
            difference = datetime.timedelta(hours=4) - (now - user_profile.last_exp_gain)
            hours, remainder = divmod(difference.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return (False, "You can check again after {} hours, {} minutes, {} seconds.".format(int(hours), int(minutes), int(seconds)))
    except ObjectDoesNotExist:
        return False


@database_sync_to_async
def get_user_from_token(token):
    return token.user
