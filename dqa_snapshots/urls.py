from django.urls import path
from . import views

urlpatterns = [
    path('', views.VariableLevelCheckListView.as_view(), name='index'),
    path('v_checks/update', views.VariableLevelCheckUpdateView.as_view()),
    path('v_checks/add', views.VariableLevelCheckCreateView.as_view()),
    path('v_checks', views.VariableLevelCheckListView.as_view()),
    path('v_checks/<int:pk>/', views.VariableLevelCheckDetailView.as_view()),
    path('v_checks/delete/<int:pk>/', views.VariableLevelCheckDestroyView.as_view()),
    path('proportions/update', views.ProportionUpdateView.as_view()),
    path('proportions/add', views.ProportionCreateView.as_view()),
    path('proportions', views.ProportionListView.as_view()),
    path('proportions/<int:pk>/', views.ProportionDetailView.as_view()),
    path('proportions/delete/<int:pk>/', views.ProportionDestroyView.as_view()),
    path('snapshots/update', views.SnapshotUpdateView.as_view()),
    path('snapshots/add', views.SnapshotCreateView.as_view()),
    path('snapshots', views.SnapshotListView.as_view()),
    path('snapshots/<int:pk>/', views.SnapshotDetailView.as_view()),
    path('snapshots/delete/<int:pk>/', views.SnapshotDestroyView.as_view()),
    path('results/update', views.ResultUpdateView.as_view()),
    path('results/add', views.ResultCreateView.as_view()),
    path('results', views.ResultListView.as_view()),
    path('results/<int:pk>/', views.ResultDetailView.as_view()),
    path('results/delete/<int:pk>/', views.ResultDestroyView.as_view())
]
