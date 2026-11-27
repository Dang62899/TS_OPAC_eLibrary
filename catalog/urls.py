from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("search-suggestions/", views.search_suggestions, name="search_suggestions"),
    path("publication/<int:pk>/", views.publication_detail, name="publication_detail"),
    path("publication/<int:pk>/upload-attachment/", views.upload_attachment, name="upload_attachment"),
    path("attachment/<int:attachment_id>/request-otp/", views.request_download_otp, name="request_download_otp"),
    path("attachment/<int:attachment_id>/unlock/", views.unlock_attachment, name="unlock_attachment"),
    path("attachment/<int:attachment_id>/download/", views.download_attachment, name="download_attachment"),
    path("attachment/<int:attachment_id>/stream/", views.stream_attachment, name="stream_attachment"),
    path("attachment/<int:attachment_id>/confirm-otp/", views.confirm_attachment_otp, name="confirm_attachment_otp"),
    path("attachment/confirm/<str:otp_code>/", views.confirm_download, name="confirm_download"),
    path("attachment/<int:attachment_id>/preview-merged/", views.preview_merged_attachment, name="preview_merged_attachment"),
    path("browse/type/<int:type_id>/", views.browse_by_type, name="browse_by_type"),
    path("browse/subject/<int:subject_id>/", views.browse_by_subject, name="browse_by_subject"),
    path("browse/author/<int:author_id>/", views.browse_by_author, name="browse_by_author"),
    path("browse/research/", views.browse_research, name="browse_research"),
    path("manage/", views.manage_publications, name="manage_publications"),
    path("add/", views.add_publication, name="add_publication"),
    path("edit/<int:pk>/", views.edit_publication, name="edit_publication"),
    path("delete/<int:pk>/", views.delete_publication, name="delete_publication"),
    path("add-items/<int:pk>/", views.add_items, name="add_items"),
]
