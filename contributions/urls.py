# Django
from django.urls import include, path, re_path

# local Django
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # re_path(r'^(?P<tag_description>[0-9])/$', views.index, name='index'),
    path('<int:commit_id>/', views.detail, name='detail'),
    path('commits/search/', views.detail_by_hash, name='detail_by_hash'),
    path('developers/<int:committer_id>/', views.detail_in_committer,),
    path('to_csv/', views.export_to_csv,),
    path('authors_to_csv/', views.export_to_csv_commit_by_author,),
    path('data_by_directory/<int:directory_id>', views.data_by_directory),
    path('<int:directory_id>/change', views.visible_directory),
]
