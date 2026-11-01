import secrets

from django.db import migrations, models

import subscribe.models


def give_each_row_a_token(apps, schema_editor):
    Subscriber = apps.get_model('subscribe', 'Subscriber')
    for subscriber in Subscriber.objects.all():
        subscriber.token = secrets.token_urlsafe(32)
        subscriber.save(update_fields=['token'])


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0003_subscriber_nickname'),
    ]

    operations = [
        # Existing rows already receive the newsletter: grandfather them as confirmed.
        migrations.AddField(
            model_name='subscriber',
            name='confirmed',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='confirmation_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # A callable default is evaluated once for AddField, so fill tokens per row
        # before making the column unique.
        migrations.AddField(
            model_name='subscriber',
            name='token',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.RunPython(give_each_row_a_token, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='subscriber',
            name='token',
            field=models.CharField(default=subscribe.models.new_token, max_length=64, unique=True),
        ),
    ]
