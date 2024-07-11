from django.db import models

from users.models import User


# Create your models here.

class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback = models.TextField()
    date_authored = models.DateTimeField()
    resolved = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'feedback'


class FeedbackPhoto(models.Model):
    feedback_photo_id = models.AutoField(primary_key=True)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    photo_file_path = models.TextField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'feedback_photos'
