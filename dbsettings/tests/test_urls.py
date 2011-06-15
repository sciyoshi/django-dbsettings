from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^settings/', include('dbsettings.urls')),
)
