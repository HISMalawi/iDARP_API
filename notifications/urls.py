from django.urls import path
from . import views

urlpatterns = [
    path('send/', views.SendNotification.as_view(), name='send'),
    path('createnotification/', views.NotificationCreateView.as_view()),
    path('<int:notification_id>/', views.PatchRequestNotificationView.as_view(), name='patch-notification'),
    path('user-notifications/', views.GetUserNotifications.as_view(), name='user-notifications')
]
