# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rango', '0009_category_testf'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='testf',
        ),
    ]
