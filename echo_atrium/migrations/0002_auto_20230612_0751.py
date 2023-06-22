from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('echo_atrium', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_exp_gain',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
