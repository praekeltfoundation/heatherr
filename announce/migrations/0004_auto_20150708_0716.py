# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('announce', '0003_auto_20150624_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, default=0, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='group',
            name='group_name',
            field=models.CharField(max_length=200),
        ),
    ]
