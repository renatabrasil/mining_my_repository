from django.urls import path

from . import views

app_name = 'architecture'

urlpatterns = [
    path('', views.index, name='index'),
    # path('<int:project_id>/compileds/', views.build_compileds, name='build_compileds'),
    path('<int:project_id>/results/', views.results, name='results'),
    path('<int:file_id>/', views.build_compileds, name='build_compileds'),
]