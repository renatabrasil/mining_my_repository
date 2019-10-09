from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # re_path(r'^(?P<tag_description>[0-9])/$', views.index, name='index'),
    path('<int:commit_id>/', views.detail, name='detail'),
    path('developers/<int:committer_id>/', views.detail_in_committer,),
    path('to_csv/', views.export_to_csv,),
    path('authors_to_csv/', views.export_to_csv_commit_by_author,),
]