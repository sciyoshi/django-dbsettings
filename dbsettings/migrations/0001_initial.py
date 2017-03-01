# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from dbsettings.settings import USE_SITES, VALUE_LENGTH


class Migration(migrations.Migration):

    dependencies = []
    if USE_SITES:
        dependencies.append(('sites', '0001_initial'))

    operations = [
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module_name', models.CharField(max_length=255)),
                ('class_name', models.CharField(max_length=255, blank=True)),
                ('attribute_name', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=VALUE_LENGTH, blank=True)),
            ] + ([('site', models.ForeignKey(to='sites.Site'))] if USE_SITES else [])
        ),
    ]
