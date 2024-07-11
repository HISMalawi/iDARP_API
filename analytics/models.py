from django.db import models


# Create your models here.

class Tag(models.Model):
    tag_id = models.AutoField(primary_key=True)
    tag = models.CharField(max_length=255)
    abbr = models.CharField(max_length=20, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'tags'

    def __str__(self):
        return f"{self.tag_id} {self.tag}"
