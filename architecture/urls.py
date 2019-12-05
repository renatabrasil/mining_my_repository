from django.urls import path

from . import views

app_name = 'architecture'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:project_id>/results/', views.results, name='results'),
    path('compileds/<int:file_id>/', views.compileds, name='compileds'),
    path('metrics/<int:file_id>/', views.calculate_metrics, name='calculate_metrics'),
    path('metrics_by_commits/', views.metrics_by_commits, name='metrics_by_commits'),
    path('metrics_by_developer/', views.metrics_by_developer, name='metrics_by_developer'),
    path('extract_metrics_csv/<int:file_id>/', views.calculate_architecture_metrics, name='calculate_architecture_metrics'),
]