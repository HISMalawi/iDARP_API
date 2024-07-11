from rest_framework import serializers
from data_exploration.models import *

class PresetSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(required=False)
    class Meta:
        model = Preset
        fields = [
            'preset_id',
            'preset_name',
            'description',
            'created_by',
            'created_on',
        ]

    def create(self, validated_data):
        
        for key, value in self.context.items():
            validated_data[key] = self.context.get(key, '')
       
        return super().create(validated_data)
    
    def get_created_by(self, obj):
        user = self.context['request'].user
        return user.user_id

class PresetVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresetVariable
        fields = [
            'preset_variable_id',
            'preset',
            'var',
            'is_distinct',
        ]


