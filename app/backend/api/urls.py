from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .upload import DocumentUploadView
from .extraction import DocumentExtractionView
from .recommendations import RecommendationRunView, TeacherDecisionView
from .notifications import NotificationListView, NotificationReadView
from .admin_views import AdminMetricsApiView
from .views import MeView, SubmissionViewSet

router = DefaultRouter()
router.register("submissions", SubmissionViewSet, basename="submission")

urlpatterns = [
    path("auth/me", MeView.as_view(), name="auth-me"),
    path("submissions/<uuid:submission_id>/documents/", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/<uuid:document_id>/extract/", DocumentExtractionView.as_view(), name="document-extract"),
    path("submissions/<uuid:submission_id>/recommendations/", RecommendationRunView.as_view(), name="recommendation-run"),
    path("recommendation-items/<uuid:item_id>/decision/", TeacherDecisionView.as_view(), name="teacher-decision"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<uuid:notification_id>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("admin/metrics/", AdminMetricsApiView.as_view(), name="admin-metrics-api"),
    path("", include(router.urls)),
]
