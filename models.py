from django.db import models

class Value(models.Model):
    app_label = models.CharField(maxlength=255)
    model = models.CharField(maxlength=255)
    name = models.CharField(maxlength=255)
    content = models.CharField(maxlength=255)

    def __nonzero__(self):
        return self.id is not None

