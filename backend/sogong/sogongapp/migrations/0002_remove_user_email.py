# Generated by Django 4.2 on 2023-05-30 12:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sogongapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='email',
        ),
    ]
