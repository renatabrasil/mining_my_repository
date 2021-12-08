# Django
from django.urls import path

# local Django
from . import views2
from .views import ContributionsView

urlpatterns = [
    path('2', views2.index, name='index'),
    path('', ContributionsView.as_view(), name='index'),
    path('<int:commit_id>/', views2.detail, name='detail'),
    path('commits/', views2.detail_by_hash, name='detail_by_hash'),
    path('developers/<int:committer_id>/', views2.detail_in_committer),
]
