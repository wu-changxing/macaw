
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_alter_homepage_options_homepage_first_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomeItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
<<<<<<< HEAD
                ('name', models.CharField(max_length=200, null=True)),
=======
                ('name', models.CharField(max_length=200)),
>>>>>>> d52712de697150d3e44a3504629ca7a4d5954acc
                ('link', models.URLField(blank=True, null=True)),
                ('intro', models.CharField(max_length=200, null=True)),
                ('fa', models.CharField(max_length=200, null=True)),
            ],
            options={
<<<<<<< HEAD
                'verbose_name': 'Item',
                'verbose_name_plural': 'Items',
=======
                'verbose_name': 'Homepage Item',
                'verbose_name_plural': 'Homepage Items',
>>>>>>> d52712de697150d3e44a3504629ca7a4d5954acc
            },
        ),
        migrations.RemoveField(
            model_name='homepage',
            name='body',
        ),
        migrations.RemoveField(
            model_name='homepage',
            name='first_description',
        ),
        migrations.RemoveField(
            model_name='homepage',
            name='first_title',
        ),
        migrations.CreateModel(
            name='HomeItemOrderable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.homeitem')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_items', to='home.homepage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]
