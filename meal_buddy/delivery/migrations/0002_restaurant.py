# Generated by Django 5.2 on 2025-04-25 14:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('image_url', models.URLField(help_text="URL of the restaurant's image", max_length=500, validators=[django.core.validators.URLValidator()])),
                ('phone', models.CharField(max_length=20)),
                ('cuisine', models.CharField(max_length=50)),
                ('opening_hours', models.CharField(max_length=100)),
                ('rating', models.IntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
            ],
        ),
    ]
