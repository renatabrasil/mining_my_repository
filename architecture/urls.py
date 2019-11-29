from django.urls import path

from . import views

app_name = 'architecture'

urlpatterns = [
    path('', views.index, name='index'),
    # path('<int:project_id>/compileds/', views.build_compileds, name='build_compileds'),
    path('<int:project_id>/results/', views.results, name='results'),
    path('compileds/<int:file_id>/', views.build_compileds, name='build_compileds'),
    path('metrics/<int:file_id>/', views.calculate_metrics, name='calculate_metrics'),
    path('architecture_metrics/', views.architecture_metrics, name='architecture_metrics'),
    path('architecture_metrics/<int:file_id>/', views.calculate_architecture_metrics, name='calculate_architecture_metrics'),
]