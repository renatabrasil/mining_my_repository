# Django
from django.urls import path

# local Django
from . import views

urlpatterns = [
    path('', views.ContributionsListView.as_view(), name='index'),
    path('<int:pk>/', views.CommitDetailView.as_view(), name='detail'),
    path('commits/', views.CommitDetailView.as_view(), name='detail_by_hash'),
    path('sentry-debug/', views.trigger_error),
]
