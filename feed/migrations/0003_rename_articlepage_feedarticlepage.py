# Generated by Django 4.0.7 on 2023-06-24 13:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0076_modellogentry_revision'),
        ('feed', '0002_feedpage'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ArticlePage',
            new_name='FeedArticlePage',
        ),
    ]
