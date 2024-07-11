from django.urls import path
from . import views

urlpatterns = [
    path('', views.FacilityListView.as_view(), name='index'),
    path('update', views.FacilityUpdateView.as_view()),
    path('add', views.FacilityCreateView.as_view()),
    path('facilities', views.FacilityListView.as_view()),
    path('<int:pk>/', views.FacilityDetailView.as_view())
]
