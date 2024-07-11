from rest_framework import serializers

from feedback.models import Feedback, FeedbackPhoto


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'


class FeedbackPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackPhoto
        fields = '__all__'
