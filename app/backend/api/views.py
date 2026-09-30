from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import Role, Submission
from reviews.models import Notification, UserProfile

from .permissions import SubmissionPermission, user_role
from .serializers import MeSerializer, SubmissionSerializer


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({"data": MeSerializer(request.user).data})


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = (SubmissionPermission,)

    def get_queryset(self):
        queryset = Submission.objects.select_related("student", "owner").order_by("-created_at")
        if user_role(self.request.user) == Role.SALES:
            return queryset.filter(owner=self.request.user)
        return queryset

    def perform_create(self, serializer):
        submission = serializer.save(owner=self.request.user)
        if submission.teacher_id:
            Notification.objects.create(
                recipient=submission.teacher,
                submission=submission,
                event_type="SUBMISSION_ASSIGNED",
                message=f"Bạn được phân công xét hồ sơ {submission.student.full_name}.",
            )
