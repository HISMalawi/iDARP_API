from rest_framework import serializers
from dqa_snapshots.models import *


class VariableLevelCheckSerializer(serializers.ModelSerializer):

    class Meta:
        model = VariableLevelCheck
        fields = '__all__'


class ProportionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Proportion
        fields = '__all__'


class SnapshotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Snapshot
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = Result
        fields = '__all__'
