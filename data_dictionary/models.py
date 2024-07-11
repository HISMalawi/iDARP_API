from django.db import models

from users.models import OrgRole, AssignedRole


# Create your models here.

class DataSource(models.Model):
    data_source_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    db_type = models.CharField(max_length=255, null=True)
    dbms = models.CharField(max_length=255, null=True)
    db_host = models.CharField(max_length=255, null=True)
    db_username = models.CharField(max_length=255, null=True)
    db_password = models.CharField(max_length=255, null=True)

    class Meta:
        managed = True
        db_table = 'data_source'

    def __str__(self):
        return f"id: {self.data_source_id} source: {self.description}"


class Topic(models.Model):
    topic_id = models.AutoField(primary_key=True)
    topic = models.CharField(max_length=65)
    description = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    active = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'topics'

    def __str__(self):
        return self.topic


class PalettePosition(models.Model):
    position_id = models.AutoField(primary_key=True)
    position = models.CharField(max_length=13)

    class Meta:
        managed = True
        db_table = 'palette_positions'

    def __str__(self):
        return self.position


class TableType(models.Model):
    table_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    position = models.ForeignKey(PalettePosition, models.DO_NOTHING, related_name='palette_positions')

    class Meta:
        managed = True
        db_table = 'table_types'

    def __str__(self):
        return self.name


class Table(models.Model):
    tbl_id = models.AutoField(primary_key=True)
    table_type = models.ForeignKey(TableType, models.DO_NOTHING, related_name='table_types')
    tbl_name = models.CharField(max_length=65)
    tbl_description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=60, blank=True, null=True)
    entity_name = models.CharField(max_length=30, null=True)
    in_PoC = models.BooleanField(null=True)
    in_eMC = models.BooleanField(null=True)
    poc_earliest_record = models.DateField(blank=True, null=True)
    emc_earliest_record = models.DateField(blank=True, null=True)
    poc_latest_record = models.DateField(blank=True, null=True)
    emc_latest_record = models.DateField(blank=True, null=True)
    poc_total_records = models.IntegerField(blank=True, null=True)
    emc_total_records = models.IntegerField(blank=True, null=True)
    poc_valid_records = models.IntegerField(blank=True, null=True)
    emc_valid_records = models.IntegerField(blank=True, null=True)
    publish = models.BooleanField(null=True)
    data_source = models.ForeignKey(DataSource, models.DO_NOTHING)

    class Meta:
        managed = True
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
        managed = True
        db_table = 'topic_tables'
        unique_together = (('topic', 'tbl'),)

    def __str__(self):
        return f"{self.topic}, {self.tbl}"


class TableMetadata(models.Model):
    metadata_id = models.AutoField(primary_key=True)
    tbl = models.ForeignKey(Table, models.DO_NOTHING)
    key = models.CharField(max_length=70)
    value = models.CharField(max_length=255)
    val_type = models.CharField(max_length=70)

    class Meta:
        managed = True
        db_table = 'table_metadata'
        unique_together = (('tbl', 'key'),)


class Edge(models.Model):
    edge_id = models.AutoField(primary_key=True)
    source = models.ForeignKey('Table', models.DO_NOTHING, db_column='source')
    destination = models.ForeignKey('Table', models.DO_NOTHING, related_name='arrow_head', db_column='destination')

    class Meta:
        managed = True
        db_table = 'edges'
        unique_together = (('source', 'destination'),)

    def __str__(self):
        return f"{self.source}, {self.destination}"


class Variable(models.Model):
    tbl = models.ForeignKey(Table, models.DO_NOTHING, related_name='var', blank=True, null=True)
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
    is_primary = models.BooleanField(blank=True, null=True, default=False)
    is_foreign = models.BooleanField(blank=True, null=True, default=False)
    value_count = models.IntegerField(blank=True, null=True)
    is_identifiable = models.BooleanField(blank=True, null=True, default=False)
    is_analytical = models.BooleanField(null=True, default=True)
    enumerated = models.BooleanField(blank=True, null=True, default=False)
    data_source = models.ForeignKey(DataSource, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'variables'

    def __str__(self):
        return self.var_name


class Dependency(models.Model):
    dep_id = models.AutoField(primary_key=True)
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='dependencies')
    depend_on = models.ForeignKey('Variable', models.DO_NOTHING, related_name='points_to', db_column='depend_on')

    class Meta:
        managed = True
        db_table = 'dependencies'
        unique_together = (('var', 'depend_on'),)

    def __str__(self):
        return f"{self.var}, {self.depend_on}"


class Synonym(models.Model):
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='synonyms')
    syn_id = models.AutoField(primary_key=True)
    synonym = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'synonyms'

    def __str__(self):
        return self.synonym


class InputValue(models.Model):
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='input_values')
    val_id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'input_values'

    def __str__(self):
        return self.value


class TimelineOfChange(models.Model):
    var = models.ForeignKey('Variable', models.DO_NOTHING, related_name='timeline_of_changes')
    change_id = models.AutoField(primary_key=True)
    change_date = models.DateTimeField()
    comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'timeline_of_change'


class ColorPalette(models.Model):
    palette_id = models.AutoField(primary_key=True)
    palette_name = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'color_palettes'

    def __str__(self):
        return self.palette_name


class Color(models.Model):
    color_id = models.AutoField(primary_key=True)
    position = models.ForeignKey(PalettePosition, models.DO_NOTHING, related_name='color_positions')
    pallete = models.ForeignKey(ColorPalette, models.DO_NOTHING, related_name='color_palettes')
    color_hex = models.CharField(max_length=10)

    class Meta:
        managed = True
        db_table = 'colors'

    def __str__(self):
        return f"{self.color_hex}, {self.pallete}"


class VariableMetadata(models.Model):
    metadata_id = models.AutoField(primary_key=True)
    variable = models.ForeignKey(Variable, models.DO_NOTHING, related_name='variable_metadata')
    key = models.CharField(max_length=255)
    value = models.TextField()
    val_type = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'variable_metadata'


class DataCustodian(models.Model):
    custodian_id = models.AutoField(primary_key=True)
    data_source = models.ForeignKey(DataSource, models.DO_NOTHING)
    org_role = models.ForeignKey(OrgRole, models.DO_NOTHING)
    broker = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'data_custodians'
        unique_together = (('data_source', 'org_role'),)

    def __str__(self):
        return f"id: {self.custodian_id} Org role: {self.org_role}"


class Version(models.Model):
    version_id = models.AutoField(primary_key=True)
    data_source = models.ForeignKey(DataSource, models.DO_NOTHING, related_name='data_source')
    date_created = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    commited_by = models.ForeignKey(AssignedRole, models.DO_NOTHING, related_name='assigned_role', blank=True,
                                    null=True)

    class Meta:
        managed = True
        db_table = 'versions'


class VersionVariable(models.Model):
    version_variable_id = models.AutoField(primary_key=True)
    version = models.ForeignKey(Version, models.DO_NOTHING, related_name='versions')
    variable = models.ForeignKey(Variable, models.DO_NOTHING, related_name='variables')

    class Meta:
        managed = True
        db_table = 'version_variables'
