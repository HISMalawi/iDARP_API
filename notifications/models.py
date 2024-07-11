from django.db import models
from data_requests.models import RequestState
from users.models import OrgRole, AssignedRole


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    message = models.TextField(default='Hello, You have unread iDARP Notifications', null=False)
    authored_on = models.DateTimeField(auto_now=True)
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=255, null=True)

    class Meta:
        managed = True
        db_table = 'notifications'


class RequestNotification(models.Model):
    request_notification_id = models.AutoField(primary_key=True)
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE)
    request_state = models.ForeignKey(RequestState, on_delete=models.CASCADE)
    request_notification_type = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'request_notifications'


class UserNotification(models.Model):
    user_notification_id = models.AutoField(primary_key=True)
    request_notification = models.ForeignKey(RequestNotification, on_delete=models.CASCADE)
    assigned_role = models.ForeignKey(AssignedRole, on_delete=models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'user_notifications'


class GroupNotification(models.Model):
    group_notification_id = models.AutoField(primary_key=True)
    request_notification = models.ForeignKey(RequestNotification, related_name='group_request', on_delete=models.CASCADE)
    org_role = models.ForeignKey(OrgRole, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'group_notifications'

