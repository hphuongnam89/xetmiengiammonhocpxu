import csv

from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import AIUsageEvent, Role, Submission, UserProfile

from .permissions import user_role


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and user_role(request.user) == Role.ADMIN)


def collect_metrics(start=None, end=None):
    submissions = Submission.objects.all()
    usage_events = AIUsageEvent.objects.all()
    profiles = UserProfile.objects.all()
    if start:
        submissions = submissions.filter(created_at__date__gte=start)
        usage_events = usage_events.filter(created_at__date__gte=start)
        profiles = profiles.filter(user__date_joined__date__gte=start)
    if end:
        submissions = submissions.filter(created_at__date__lte=end)
        usage_events = usage_events.filter(created_at__date__lte=end)
        profiles = profiles.filter(user__date_joined__date__lte=end)
    return {
        "submissions": list(submissions.values("status").annotate(total=Count("id")).order_by("status")),
        "users": list(profiles.values("role").annotate(total=Count("id")).order_by("role")),
        "usage": list(
            usage_events.values("provider", "model_name", "operation")
            .annotate(input_tokens=Sum("input_tokens"), output_tokens=Sum("output_tokens"), cost=Sum("cost"), requests=Count("id"))
            .order_by("provider", "model_name", "operation")
        ),
        "user_total": profiles.count(),
    }


def _date_filters(request):
    start_raw, end_raw = request.GET.get("start", ""), request.GET.get("end", "")
    start, end = parse_date(start_raw) if start_raw else None, parse_date(end_raw) if end_raw else None
    if (start_raw and start is None) or (end_raw and end is None) or (start and end and start > end):
        return None, None, "Ngày lọc không hợp lệ."
    return start, end, None


class AdminMetricsApiView(APIView):
    permission_classes = (IsAuthenticated, IsAdminRole)

    def get(self, request):
        start, end, error = _date_filters(request)
        if error:
            return Response({"error": {"code": "invalid_date_range", "message": error}}, status=400)
        return Response({"data": collect_metrics(start, end)})


@login_required
def admin_metrics_page(request):
    if user_role(request.user) != Role.ADMIN:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Admin only.")
    start, end, error = _date_filters(request)
    context = {"metrics": collect_metrics(start, end), "start": request.GET.get("start", ""), "end": request.GET.get("end", ""), "error": error}
    return render(request, "reviews/admin_metrics.html", context)


@login_required
def admin_metrics_csv(request):
    if user_role(request.user) != Role.ADMIN:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Admin only.")
    start, end, error = _date_filters(request)
    if error:
        return HttpResponse(error, status=400, content_type="text/plain; charset=utf-8")
    metrics = collect_metrics(start, end)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="admin-metrics.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["category", "provider", "model", "operation", "status_or_role", "requests_or_total", "input_tokens", "output_tokens", "cost"])
    for row in metrics["submissions"]:
        writer.writerow(["submission", "", "", "", row["status"], row["total"], "", "", ""])
    for row in metrics["users"]:
        writer.writerow(["users", "", "", "", row["role"], row["total"], "", "", ""])
    for row in metrics["usage"]:
        writer.writerow(["ai_usage", row["provider"], row["model_name"], row["operation"], "", row["requests"], row["input_tokens"] or 0, row["output_tokens"] or 0, row["cost"] or 0])
    return response
