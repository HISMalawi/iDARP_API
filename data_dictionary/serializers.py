from rest_framework import serializers
from data_dictionary.models import *
from django.db.models import Q
import json


class TimelineOfChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineOfChange
        fields = [
            'change_id',
            'change_date',
            'comment',
        ]


class DependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependency
        fields = [
            'depend_on',
        ]


class InputValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = InputValue
        fields = [
            'val_id',
            'value',
        ]


class SynonymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Synonym
        fields = [
            'syn_id',
            'synonym',
        ]


class VariableMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableMetadata
        fields = '__all__'


class VariableSerializer(serializers.ModelSerializer):
    synonyms = SynonymSerializer(many=True)
    input_values = InputValueSerializer(many=True)
    dependencies = DependencySerializer(many=True)
    timeline_of_changes = TimelineOfChangeSerializer(many=True)
    variable_metadata = VariableMetadataSerializer(many=True)

    class Meta:
        model = Variable
        fields = '__all__'


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = [
            'source',
            'destination',
        ]
        depth = 1


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = [
            'color_id',
            'position',
            'pallete',
            'color_hex'
        ]
        depth = 1


class PalettePositionSerializer(serializers.ModelSerializer):
    color_positions = ColorSerializer(many=True)

    class Meta:
        model = PalettePosition
        fields = [
            'position_id',
            'position',
            'color_positions'
        ]


class TableTypeSerializer(serializers.ModelSerializer):
    position = PalettePositionSerializer()

    class Meta:
        model = TableType
        fields = [
            'table_type_id',
            'name',
            'position',
        ]


class TableSerializer(serializers.ModelSerializer):
    var = VariableSerializer(many=True)
    table_type = TableTypeSerializer(many=False)

    class Meta:
        model = Table
        fields = [
            'tbl_id',
            'tbl_name',
            'tbl_description',
            'var',
            'icon',
            'entity_name',
            'in_PoC',
            'in_eMC',
            'poc_earliest_record',
            'emc_earliest_record',
            'poc_latest_record',
            'emc_latest_record',
            'poc_total_records',
            'emc_total_records',
            'poc_valid_records',
            'emc_valid_records',
            'publish',
            'table_type',
            'data_source'
        ]


class TopicTableSerializer(serializers.ModelSerializer):
    tbl = TableSerializer(many=False)

    class Meta:
        model = TopicTable
        fields = [
            'topic',
            'tbl',
            'assigned_on',
            'pos_x',
            'pos_y',
        ]


class TopicSerializer(serializers.ModelSerializer):
    tables = TopicTableSerializer(many=True)

    class Meta:
        model = Topic
        fields = [
            'topic_id',
            'topic',
            'description',
            'date_added',
            'active',
            'tables'
        ]


class ColorPaletteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorPalette
        fields = [
            'palette_id',
            'palette_name'
        ]


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = '__all__'


class DataSourceTreeSerializer(serializers.ModelSerializer):
    table_set = TableSerializer(many=True, read_only=True)

    class Meta:
        model = DataSource
        fields = [
            'data_source_id',
            'source',
            'description',
            'db_type',
            'dbms',
            'db_host',
            'db_username',
            'db_password',
            'table_set'
        ]
