from django.db import models

from users.models import User


# Create your models here.

class Setting(models.Model):
    setting_id = models.AutoField(primary_key=True)
    setting = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255)
    default_value = models.CharField(max_length=255)

    def __str__(self):
        return f"|{self.setting_id} \t| {self.setting} \t| {self.data_type} \t| {self.default_value}"

    class Meta:
        db_table = 'settings'
        managed = True


class UserSetting(models.Model):
    user_setting_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    setting_value = models.CharField(max_length=255)

    def __str__(self):
        return f"|{self.user.fname} {self.user.sname} \t| {self.setting.setting} = {self.setting_value} \t|"

    class Meta:
        db_table = 'user_settings'
        managed = True
