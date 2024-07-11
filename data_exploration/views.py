from data_exploration.models import *
from data_exploration.serializers import *
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework import permissions

from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import ValidationError
import json

import logging
# Create your views here.

logger = logging.getLogger(__name__)


class PresetView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Preset.objects.all()
    serializer_class = PresetSerializer

    def get_queryset(self):
        return self.queryset.all()  

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and hasattr(exc, 'get_codes'):
            if 'preset_name' in exc.get_codes():
                error_message = "Preset with this preset name already exists."
            elif 'created_by' in exc.get_codes():
                error_message = "Invalid user id."
            else:
                return super().handle_exception(exc)
            return Response({'code': '400', 'message': error_message}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        preset_id = self.request.query_params.get('preset_id')
        
        if preset_id:

            try:
                preset = Preset.objects.get(preset_id=preset_id)
                queryset = queryset.filter(preset_id=preset.preset_id)

            except Preset.DoesNotExist:
                return Response({'code': '400', 'message': 'Preset not found'}, status=status.HTTP_200_OK)
        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'created_by': request.user, })
        serializer.is_valid(raise_exception=True)
        preset_data = serializer.validated_data  # Retrieve the validated data from the serializer
        preset = serializer.save()

        preset_data['preset_id'] = preset.pk

        return Response({
            'code': '201',
            'message': 'Preset created successfully',
            'preset': preset_data  
        }, status=status.HTTP_201_CREATED)


class PresetVariablesView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = PresetVariable.objects.all()
    serializer_class = PresetVariableSerializer

    def get_queryset(self):
        return self.queryset.all() 

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and hasattr(exc, 'get_codes'):
            if 'non_field_errors' in exc.get_codes():
                error_message = "Variable already exists."
            elif 'preset' in exc.get_codes():
                error_message = "Invalid preset id."
            elif 'var' in exc.get_codes():
                error_message = "Invalid variable id."
            else:
                return super().handle_exception(exc)
            return Response({'code': '400', 'message': error_message}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        preset_id = self.request.query_params.get('preset_id')

        if preset_id:

            try:
                preset = Preset.objects.get(preset_id=preset_id)
                queryset = queryset.filter(preset=preset)

            except Preset.DoesNotExist:
                return Response({'code': '400', 'message': 'Preset not found'}, status=status.HTTP_200_OK)
        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        preset_variable_data = serializer.validated_data
        preset_variable = serializer.save()

        data = {
            'preset_variable_id': preset_variable.pk,
            'preset_id': preset_variable_data['preset'].preset_id,
            'is_distinct': preset_variable_data['is_distinct'],
        }
  
        return Response({'code': '201', 'message': 'Preset variable added successfully', 'preset_variable': data},
                        status=status.HTTP_201_CREATED)
