from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:commit_id>/', views.detail, name='detail'),
    path('developers/<int:committer_id>/', views.detail_in_committer,),
]