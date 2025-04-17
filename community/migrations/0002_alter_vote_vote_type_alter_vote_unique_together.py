# Generated by Django 5.1.5 on 2025-02-04 07:45

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='vote_type',
            field=models.IntegerField(choices=[(1, 'Upvote'), (-1, 'Downvote')]),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together={('user', 'post')},
        ),
    ]
