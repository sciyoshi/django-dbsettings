from django.db import models

class Value(models.Model):
    module_name = models.CharField(maxlength=255)
    class_name = models.CharField(maxlength=255, blank=True)
    attribute_name = models.CharField(maxlength=255)
    content = models.CharField(maxlength=255)

    def __nonzero__(self):
        return self.id is not None

