# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-16 17:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailforms', '0003_capitalizeverbose'),
        ('wagtailcore', '0039_collectionviewrestriction'),
        ('wagtailredirects', '0005_capitalizeverbose'),
        ('cms', '0006_setup_helpsite'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='apppage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='helpindex',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='helppage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='peoplepage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='personinfo',
            name='image',
        ),
        migrations.RemoveField(
            model_name='personinfo',
            name='page',
        ),
        migrations.DeleteModel(
            name='AppPage',
        ),
        migrations.DeleteModel(
            name='HelpIndex',
        ),
        migrations.DeleteModel(
            name='HelpPage',
        ),
        migrations.DeleteModel(
            name='PeoplePage',
        ),
        migrations.DeleteModel(
            name='PersonInfo',
        ),
    ]
