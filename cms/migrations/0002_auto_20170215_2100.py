# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-02-15 21:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apppage',
            name='description',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='helppage',
            name='description',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='peoplepage',
            name='description',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
    ]
