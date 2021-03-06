# Generated by Django 4.0.3 on 2022-04-15 16:18

from django.db import migrations, models
import public_chat.models


class Migration(migrations.Migration):

    dependencies = [
        ('public_chat', '0002_publicchatroom_registered_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicchatroom',
            name='profile_image',
            field=models.ImageField(blank=True, default=public_chat.models.get_default_profile_image, max_length=255, null=True, upload_to=public_chat.models.get_profile_image_filepath),
        ),
    ]
