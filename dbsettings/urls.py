from django.conf.urls.defaults import *

urlpatterns = patterns('dbsettings.views',
    url(r'^$', 'site_settings', name='site_settings'),
    url(r'^(?P<app_label>[^/]+)/$', 'app_settings', name='app_settings'),
)
