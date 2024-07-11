from django.contrib import admin
from notifications.models import *

# Register your models here.
admin.site.register(Notification)
admin.site.register(GroupNotification)
admin.site.register(UserNotification)
admin.site.register(RequestNotification)