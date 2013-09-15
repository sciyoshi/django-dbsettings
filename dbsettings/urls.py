try:
    from django.conf.urls import patterns, url
except ImportError:
    # Django 1.3
    from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('dbsettings.views',
    url(r'^$', 'site_settings', name='site_settings'),
    url(r'^(?P<app_label>[^/]+)/$', 'app_settings', name='app_settings'),
)
