from django.urls import path

from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.index, name='index'),
    # path('population_means/', views.population_means, name='population_means'),
    path('descriptive_statistics/<int:type>/', views.descriptive_statistics, name='descriptive_statistics'),
]
