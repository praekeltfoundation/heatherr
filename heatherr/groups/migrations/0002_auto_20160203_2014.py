# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-02-03 20:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slackaccount',
            field=models.ForeignKey(default=-1, on_delete=django.db.models.deletion.CASCADE, to='heatherr.SlackAccount'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='person',
            name='slackaccount',
            field=models.ForeignKey(default=-1, on_delete=django.db.models.deletion.CASCADE, to='heatherr.SlackAccount'),
            preserve_default=False,
        ),
    ]
