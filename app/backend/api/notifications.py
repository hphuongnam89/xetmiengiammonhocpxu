from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import Notification


class NotificationListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        items = Notification.objects.filter(recipient=request.user)[:100]
        return Response({"data": [self.serialize(item) for item in items]})

    @staticmethod
    def serialize(item):
        return {"id": str(item.id), "event_type": item.event_type, "message": item.message,
                "submission_id": str(item.submission_id) if item.submission_id else None,
                "read": item.read_at is not None, "created_at": item.created_at.isoformat()}


class NotificationReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, notification_id):
        item = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
        if item.read_at is None:
            item.read_at = timezone.now()
            item.save(update_fields=["read_at"])
        return Response({"data": NotificationListView.serialize(item)})
