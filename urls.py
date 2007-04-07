from django.conf.urls.defaults import *

urlpatterns = patterns('vgmix3.values.views',
    (r'^$', 'index'),
    (r'view/$', 'view'),
)
