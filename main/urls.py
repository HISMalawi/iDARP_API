"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from rest_framework import routers
from settings import views as settings_views

router = routers.DefaultRouter()
router.register(r'api/v1/settings', settings_views.SettingView)
router.register(r'api/v1/user-setting', settings_views.UserSettingView)

urlpatterns = [
    path('', RedirectView.as_view(url='/admin')),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/data_dictionary/', include('data_dictionary.urls')),
    path('api/v1/data_requests/', include('data_requests.urls')),
    path('api/v1/data_exploration/', include('data_exploration.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/facilities/', include('facilities.urls')),
    path('api/v1/dqa_snapshots/', include('dqa_snapshots.urls')),
]

urlpatterns += router.urls
