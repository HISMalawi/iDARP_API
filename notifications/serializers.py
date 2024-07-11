import logging
from rest_framework import serializers
from notifications.models import RequestNotification, GroupNotification, UserNotification, Notification

logger = logging.getLogger(__name__)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class RequestNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestNotification
        fields = '__all__'


class GroupNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        modal = GroupNotification
        fields = '__all__'


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        modal = UserNotification
        fields = '__all__'
