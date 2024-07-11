from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    deleted_on = models.DateTimeField(blank=True, null=True)

    def soft_delete(self):
        self.deleted_on = timezone.now()
        self.save()

    def is_delete(self):
        return self.deleted_on is not None

    class Meta:
        abstract = True
