# Django
from django.urls import path

# local Django
from . import views

app_name = 'architecture'

urlpatterns = [
    path('', views.ArchitectureListView.as_view(), name='index'),
    path('compileds/<int:file_id>/', views.ArchitecturalMetricsView.as_view(), name='compileds'),
    path('metrics/<int:file_id>/', views.ArchitecturalMetricsView.as_view(), name='calculate_metrics'),
    path('quality_between_versions/', views.ArchitecturalMetricsView.as_view(), name='quality_between_versions'),
    path('impactful_commits/', views.ImpactfulCommitsMetricsView.as_view(), name='impactful_commits'),
    path('extract_metrics_csv/<int:file_id>/', views.ArchitecturalMetricsView.as_view(),
         name='calculate_architecture_metrics'),
]
