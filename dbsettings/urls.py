from django.conf.urls import url

from dbsettings.views import site_settings, app_settings


urlpatterns = [
    url(r'^$', site_settings, name='site_settings'),
    url(r'^(?P<app_label>[^/]+)/$', app_settings, name='app_settings'),
]
