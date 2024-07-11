from django.db import models


# Create your models here.

class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)
    site_id = models.IntegerField(unique=True)
    facility = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    partner_name = models.CharField(max_length=255)
    site_name = models.CharField(max_length=255)
    emr_type = models.CharField(max_length=255)
    funding_agency = models.CharField(max_length=255)
    cdc_region = models.CharField(max_length=255)
    zone = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    orgunit = models.CharField(max_length=255)
    date_synced = models.DateTimeField(auto_now=True)
    district = models.CharField(max_length=255, default='None')

    class Meta:
        db_table = 'facilities'
        managed = True

    def __str__(self):
        return f"facility_id : {self.pk}"
