from django.db import models

# Create your models here.
class Topic(models.Model):
    topic_id = models.AutoField(primary_key=True)
    topic = models.CharField(max_length=65)
    description = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField()
    active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'topics'

    def __str__(self):
        return self.topic
    

class Table(models.Model):
    tbl_id = models.AutoField(primary_key=True)
    tbl_name = models.CharField(max_length=65)
    tbl_description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=30, blank=True, null=True)
    color = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tables'

    def __str__(self):
        return self.tbl_name


class TopicTable(models.Model):
    tt_id = models.AutoField(primary_key=True)
    topic = models.ForeignKey(Topic, models.DO_NOTHING, related_name='tables')
    tbl = models.ForeignKey(Table, models.DO_NOTHING)
    assigned_on = models.DateTimeField()
    pos_x = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pos_y = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'topic_tables'
        unique_together = (('topic', 'tbl'),)

    def __str__(self):
        return f"{self.topic}, {self.tbl}"


class Edge(models.Model):
    edge_id = models.AutoField(primary_key=True)
    source = models.ForeignKey('Table', models.DO_NOTHING, db_column='source')
    destination = models.ForeignKey('Table', models.DO_NOTHING, related_name='arrow_head', db_column='destination')

    class Meta:
        managed = False
        db_table = 'edges'
        unique_together = (('source', 'destination'),)

    def __str__(self):
        return f"{self.source}, {self.destination}"


class Variable(models.Model):
    tbl = models.ForeignKey(Table, models.DO_NOTHING, related_name='var')
    var_id = models.AutoField(primary_key=True)
    ids_column_name = models.CharField(db_column='IDS_column_name', max_length=65)  # Field name made lowercase.
    var_name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=35, blank=True, null=True)
    meaning = models.TextField(blank=True, null=True)
    date_introduced = models.DateField()
    range = models.CharField(max_length=30, blank=True, null=True)
    old_var_name = models.CharField(max_length=255, blank=True, null=True)
    reference = models.IntegerField(blank=True, null=True)
    derived = models.BooleanField(blank=True, null=True)
    usage = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'variables'

    def __str__(self):
        return self.var_name


class Dependency(models.Model):
    dep_id = models.AutoField(primary_key=True)
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='dependencies')
    depend_on = models.ForeignKey('Variable', models.DO_NOTHING, related_name='points_to', db_column='depend_on')

    class Meta:
        managed = False
        db_table = 'dependencies'
        unique_together = (('var', 'depend_on'),)

    def __str__(self):
        return f"{self.var}, {self.depend_on}"
    

class Synonym(models.Model):
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='synonyms')
    syn_id = models.AutoField(primary_key=True)
    synonym = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'synonyms'

    def __str__(self):
        return self.synonym


class InputValue(models.Model):
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='input_values')
    val_id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'input_values'

    def __str__(self):
        return self.value


class TimelineOfChange(models.Model):
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='timeline_of_changes')
    change_id = models.AutoField(primary_key=True)
    change_date = models.DateTimeField()
    comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'timeline_of_change'