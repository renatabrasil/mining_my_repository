# Django
from django.urls import path

# local Django
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # re_path(r'^(?P<tag_description>[0-9])/$', views.index, name='index'),
    path('<int:commit_id>/', views.detail, name='detail'),
    path('commits/search/', views.detail_by_hash, name='detail_by_hash'),
    path('developers/<int:committer_id>/', views.detail_in_committer,),
    path('<int:directory_id>/change', views.visible_directory),
]
