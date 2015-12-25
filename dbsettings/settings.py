from django.apps import apps
from django.conf import settings


sites_installed = apps.is_installed('django.contrib.sites')
USE_SITES = getattr(settings, 'DBSETTINGS_USE_SITES', sites_installed)
USE_CACHE = getattr(settings, 'DBSETTINGS_USE_CACHE', True)
VALUE_LENGTH = getattr(settings, 'DBSETTINGS_VALUE_LENGTH', 255)
