from django.conf import settings
try:
    from django.apps import apps
    APPS_REGISTRY = True
except ImportError:
    APPS_REGISTRY = False


sites_installed = (apps.is_installed('django.contrib.sites') if APPS_REGISTRY else
                   'django.contrib.sites' in settings.INSTALLED_APPS)
USE_SITES = getattr(settings, 'DBSETTINGS_USE_SITES', sites_installed)
