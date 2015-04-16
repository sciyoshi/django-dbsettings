from django.db import models
from django.contrib.sites.models import Site


class SettingManager(models.Manager):
    def get_queryset(self):
        sup = super(SettingManager, self)
        qs = sup.get_queryset() if hasattr(sup, 'get_queryset') else sup.get_query_set()
        return qs.filter(site=Site.objects.get_current())
    get_query_set = get_queryset


class Setting(models.Model):
    site = models.ForeignKey(Site)
    module_name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255, blank=True)
    attribute_name = models.CharField(max_length=255)
    value = models.CharField(max_length=255, blank=True)

    objects = SettingManager()

    def __bool__(self):
        return self.pk is not None

    def save(self, *args, **kwargs):
        self.site = Site.objects.get_current()
        return super(Setting, self).save(*args, **kwargs)
