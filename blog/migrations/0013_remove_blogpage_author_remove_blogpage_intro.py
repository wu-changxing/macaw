
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_blogauthorsorderable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blogpage',
            name='author',
        ),
        migrations.RemoveField(
            model_name='blogpage',
            name='intro',
        ),
    ]
