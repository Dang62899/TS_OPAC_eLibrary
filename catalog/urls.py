from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("publication/<int:pk>/", views.publication_detail, name="publication_detail"),
    path("browse/type/<int:type_id>/", views.browse_by_type, name="browse_by_type"),
    path("browse/subject/<int:subject_id>/", views.browse_by_subject, name="browse_by_subject"),
    path("browse/author/<int:author_id>/", views.browse_by_author, name="browse_by_author"),
    path("manage/", views.manage_publications, name="manage_publications"),
    path("add/", views.add_publication, name="add_publication"),
    path("edit/<int:pk>/", views.edit_publication, name="edit_publication"),
    path("delete/<int:pk>/", views.delete_publication, name="delete_publication"),
    path("add-items/<int:pk>/", views.add_items, name="add_items"),
]
