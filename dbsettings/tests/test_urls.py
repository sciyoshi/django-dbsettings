try:
    from django.conf.urls import patterns, include
except ImportError:
    # Django 1.3
    from django.conf.urls.defaults import patterns, include
from django.contrib import admin

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    (r'^settings/', include('dbsettings.urls')),
)
