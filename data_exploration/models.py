from django.db import models
from users.models import User
from data_dictionary.models import Variable

# Create your models here.

class Filter(models.Model):
    filter_id = models.AutoField(primary_key=True)
    filter_type = models.CharField(max_length=128)
    created_by = models.ForeignKey(User, models.DO_NOTHING)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'filters'

    def __str__(self):
        return f"id: {self.filter_id} type: {self.filter_type}"
    

class VariableFilter(models.Model):
    variable_filter_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey(Filter, models.DO_NOTHING)
    var_id = models.ForeignKey(Variable, models.DO_NOTHING)
    description = models.TextField()

    class Meta:
        managed = True
        db_table = 'variable_filters'

    def __str__(self):
        return f"id: {self.filter_id} variable: {str(self.var_id)}"
    

class Preset(models.Model):
    preset_id = models.AutoField(primary_key=True)
    preset_name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    created_by = models.ForeignKey(User, models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        managed = True
        db_table = 'presets'

    def __str__(self):
        return f"id: {self.preset_id} name: {self.preset_name}"
    

class PresetVariable(models.Model):
    preset_variable_id = models.AutoField(primary_key=True)
    preset = models.ForeignKey(Preset,models.DO_NOTHING)
    var = models.ForeignKey(Variable, models.DO_NOTHING)
    is_distinct = models.BooleanField()
    

    class Meta:
        managed = True
        db_table = 'preset_variables'
        unique_together = (('preset', 'var'),)

    def __str__(self):
        return f"id: {self.preset_variable_id} preset: {str(self.preset)}"
    

class PresetFilter(models.Model):
    preset_filter_id = models.AutoField(primary_key=True)
    preset = models.ForeignKey(Preset, models.DO_NOTHING)
    filter = models.ForeignKey(Filter, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'preset_filter'

    def __str__(self):
        return f"id: {self.preset_filter_id} preset: {str(self.preset)} filter: {str(self.filter)}"