from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'', views.SettingView)
router.register(r'user-setting', views.UserSettingView)

urlpatterns = [
    path('', include(router.urls))
]

urlpatterns += router.urls
