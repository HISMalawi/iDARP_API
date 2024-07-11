from django.db import models
from data_dictionary.models import Variable


# Create your models here.
class VariableLevelCheck(models.Model):
    vld_id = models.AutoField(primary_key=True)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    dqa_check_id = models.IntegerField(unique=True)
    description = models.TextField()

    class Meta:
        db_table = 'variable_level_checks'
        managed = True

    def __str__(self):
        return f"{self.dqa_check_id} : {self.description}"


class Proportion(models.Model):
    proportion_id = models.AutoField(primary_key=True)
    variable_level_check = models.ForeignKey(VariableLevelCheck, on_delete=models.CASCADE)
    proportion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'proportions'
        managed = True

    def __str__(self):
        return f"{self.proportion_id} : {self.proportion}"


class Snapshot(models.Model):
    snapshot_id = models.AutoField(primary_key=True)
    as_of = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'snapshots'
        managed = True

    def __str__(self):
        return f"Snapshot as of : {self.as_of}"


class Result(models.Model):
    result_id = models.AutoField(primary_key=True)
    proportion = models.ForeignKey(Proportion, on_delete=models.CASCADE)
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    numerator = models.IntegerField(default=0)
    denominator = models.IntegerField(default=0)

    class Meta:
        db_table = 'results'
        managed = True

    def __str__(self):
        return f"Numerator: {self.numerator}"
