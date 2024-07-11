from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response

from settings.models import Setting, UserSetting
from settings.serializers import SettingSerializer, UserSettingSerializer
from users.models import User


# Create your views here.

class SettingView(viewsets.ModelViewSet):
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Custom logic for creating a Settings record
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Custom logic for creating UserSettings for each user
        setting = serializer.instance
        users = User.objects.all()

        for user in users:
            UserSetting.objects.create(user=user, setting=setting, setting_value=setting.default_value)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)


class UserSettingView(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = UserSetting.objects.all()
    serializer_class = UserSettingSerializer

