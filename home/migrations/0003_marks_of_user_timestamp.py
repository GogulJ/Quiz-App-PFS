# Generated by Django 5.1.2 on 2024-11-14 08:25

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_remove_marks_of_user_attended_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='marks_of_user',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
