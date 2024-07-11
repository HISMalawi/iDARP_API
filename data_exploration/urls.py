from django.urls import path
from . import views

urlpatterns = [
    path('presets/', views.PresetView.as_view()),
    path('preset_variables/', views.PresetVariablesView.as_view()),
]
