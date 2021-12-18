# Django
from django.urls import path

# local Django
from . import views2, views

urlpatterns = [
    path('2', views2.index, name='index'),
    path('', views.ContributionsListView.as_view(), name='index'),
    path('<int:pk>/', views.CommitDetailView.as_view(), name='detail'),
    path('commits/', views.CommitDetailView.as_view(), name='detail_by_hash'),
]
