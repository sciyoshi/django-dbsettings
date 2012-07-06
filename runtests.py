#!/usr/bin/env python
from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.core.management import call_command


INSTALLED_APPS = (
    # Required contrib apps.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.sessions',
    # Our app and it's test app.
    'dbsettings',
)

SETTINGS = {
    'INSTALLED_APPS': INSTALLED_APPS,
    'SITE_ID': 1,
    'ROOT_URLCONF': 'dbsettings.tests.test_urls',
}

if DJANGO_VERSION > (1, 2):
    # Post multi-db settings.
    SETTINGS['DATABASES'] = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Pre multi-db settings.
    SETTINGS['DATABASE_ENGINE'] = 'sqlite3'
    SETTINGS['DATABASE_NAME'] = ':memory:'

if not settings.configured:
    settings.configure(**SETTINGS)

call_command('test', 'dbsettings')
