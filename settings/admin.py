from django.contrib import admin

from settings.models import Setting, UserSetting

# Register your models here.

admin.site.register(Setting)
admin.site.register(UserSetting)
