# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('announce', '0002_auto_20150624_1110'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='id',
        ),
        migrations.AddField(
            model_name='person',
            name='person_id',
            field=models.CharField(
                default=datetime.datetime(2015, 6, 24, 12, 31, 29, 668430,
                                          tzinfo=utc),
                max_length=200,
                serialize=False,
                primary_key=True),
            preserve_default=False,
        ),
    ]
