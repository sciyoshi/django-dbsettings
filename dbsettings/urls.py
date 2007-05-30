from django.conf.urls.defaults import *

urlpatterns = patterns('dbsettings.views',
    (r'^$', 'site_settings'),
    (r'^(?P<app_label>[^/]+)/$', 'app_settings'),
)
