#!/usr/bin/env python
import os
import sys

from django import VERSION as DJANGO_VERSION
from django.conf import settings


INSTALLED_APPS = (
    # Required contrib apps.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.sessions',
    # Our app and it's test app.
    'dbsettings',
    'dbsettings.tests'
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

from django.test.simple import run_tests


def runtests(*test_args):
    if not test_args:
        test_args = ['tests']
    parent = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
    )
    sys.path.insert(0, parent)
    failures = run_tests(test_args, verbosity=1, interactive=True)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
