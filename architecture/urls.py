# Django
from django.urls import path

# local Django
from . import views2, views

app_name = 'architecture'

urlpatterns = [
    path('', views.ArchitectureListView.as_view(), name='index'),
    path('compileds/<int:file_id>/', views.ArchitecturalMetricsView.as_view(), name='compileds'),
    path('metrics/<int:file_id>/', views2.calculate_metrics, name='calculate_metrics'),
    path('metrics_by_commits/', views2.metrics_by_commits, name='metrics_by_commits'),
    path('metrics_by_developer/', views2.metrics_by_developer, name='metrics_by_developer'),
    path('quality_between_versions/', views2.quality_between_versions, name='quality_between_versions'),
    path('impactful_commits/', views2.impactful_commits, name='impactful_commits'),
    path('extract_metrics_csv/<int:file_id>/', views2.calculate_architecture_metrics,
         name='calculate_architecture_metrics'),
]
