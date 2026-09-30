from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path
from api.web import create_submission, dashboard, mark_notification_read, preview_degree_name, review_submission, upload_submission_document, review_extraction, view_document
from api.admin_views import admin_metrics_csv, admin_metrics_page
from api.auth_views import RateLimitedLoginView


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("accounts/login/", RateLimitedLoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("app/", dashboard, name="dashboard"),
    path("app/admin/metrics/", admin_metrics_page, name="admin-metrics"),
    path("app/admin/metrics.csv", admin_metrics_csv, name="admin-metrics-csv"),
    path("app/submissions/new/", create_submission, name="create-submission"),
    path("app/submissions/preview-degree-name/", preview_degree_name, name="preview-degree-name"),
    path("app/submissions/<uuid:submission_id>/documents/", upload_submission_document, name="upload-submission-document"),
    path("app/notifications/<uuid:notification_id>/read/", mark_notification_read, name="mark-notification-read"),
    path("app/submissions/<uuid:submission_id>/review/", review_submission, name="review-submission"),
    path("app/documents/<uuid:document_id>/view/", view_document, name="view-document"),
    path("app/documents/<uuid:document_id>/extraction/", review_extraction, name="review-extraction"),
    path("health/", health),
]
