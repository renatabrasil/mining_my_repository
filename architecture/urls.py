# Django
from django.urls import path

# local Django
from . import views

app_name = 'architecture'

urlpatterns = [
    path('', views.index, name='index'),
    path('compileds/<int:file_id>/', views.compiled, name='compileds'),
    path('metrics/<int:file_id>/', views.calculate_metrics, name='calculate_metrics'),
    path('metrics_by_commits/', views.metrics_by_commits, name='metrics_by_commits'),
    path('metrics_by_developer/', views.metrics_by_developer, name='metrics_by_developer'),
    path('quality_between_versions/', views.quality_between_versions, name='quality_between_versions'),
    path('impactful_commits/', views.impactful_commits, name='impactful_commits'),
    path('extract_metrics_csv/<int:file_id>/', views.calculate_architecture_metrics,
         name='calculate_architecture_metrics'),
]
