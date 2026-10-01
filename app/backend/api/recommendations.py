from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import (
    AuditEvent,
    CurriculumVersion,
    RecommendationItem,
    RecommendationRun,
    Role,
    RuleVersion,
    Submission,
    Notification,
    TeacherDecision,
)

from .permissions import user_role
from .recommendation_service import RecommendationInputError, create_recommendation_run


def _forbidden():
    return Response({"error": {"code": "forbidden", "message": "Not allowed."}}, status=403)


class RecommendationRunView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, submission_id):
        submission = get_object_or_404(Submission, pk=submission_id)
        role = user_role(request.user)
        if role == Role.SALES and submission.owner_id != request.user.id:
            return _forbidden()
        if role not in {Role.ADMIN, Role.SALES}:
            return _forbidden()
        try:
            rule = RuleVersion.objects.get(pk=request.data.get("rule_version_id"))
            curriculum = CurriculumVersion.objects.get(pk=request.data.get("curriculum_version_id"))
        except (RuleVersion.DoesNotExist, CurriculumVersion.DoesNotExist, ValidationError, ValueError, TypeError):
            return Response({"error": {"code": "version_unavailable", "message": "Rule or curriculum version is unavailable."}}, status=422)
        key = str(request.data.get("idempotency_key", "")).strip()
        row_ids = request.data.get("course_row_ids")
        if not isinstance(row_ids, list) or any(not isinstance(value, str) for value in row_ids):
            return Response({"error": {"code": "course_rows_required", "message": "Select verified course rows."}}, status=422)
        try:
            run, created = create_recommendation_run(
                submission=submission, actor=request.user, rule=rule, curriculum=curriculum,
                course_row_ids=row_ids, idempotency_key=key,
            )
        except RecommendationInputError as exc:
            return Response({"error": {"code": exc.code, "message": str(exc)}}, status=422)
        return Response({"data": self._serialize(run)}, status=201 if created else 200)

    @staticmethod
    def _serialize(run):
        return {
            "id": str(run.id),
            "status": run.status,
            "curriculum_version_id": str(run.curriculum_version_id) if run.curriculum_version_id else None,
            "items": [
                {"id": str(item.id), "course_code": item.course_code, "recommendation": item.recommendation,
                 "confidence": str(item.confidence) if item.confidence is not None else None,
                 "rationale": item.rationale, "evidence": item.evidence}
                for item in run.items.all()
            ],
        }


class TeacherDecisionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, item_id):
        item = get_object_or_404(RecommendationItem.objects.select_related("run__submission"), pk=item_id)
        submission = item.run.submission
        role = user_role(request.user)
        if role == Role.TEACHER and submission.teacher_id != request.user.id:
            return _forbidden()
        if role not in {Role.ADMIN, Role.TEACHER}:
            return _forbidden()
        active_run = submission.recommendation_runs.filter(is_current=True).first()
        if active_run is None or active_run.id != item.run_id:
            return Response({"error": {"code": "stale_recommendation", "message": "Only the current recommendation run can be decided."}}, status=409)
        decision = str(request.data.get("decision", "")).upper()
        if decision not in {"FULL", "PARTIAL", "NOT_ELIGIBLE"}:
            return Response({"error": {"code": "invalid_decision", "message": "Unsupported decision."}}, status=422)
        reason = str(request.data.get("reason", "")).strip()
        if decision != item.recommendation and not reason:
            return Response({"error": {"code": "reason_required", "message": "Reason is required for an override."}}, status=422)
        final, _ = TeacherDecision.objects.update_or_create(
            item=item,
            defaults={"teacher": request.user, "decision": decision, "reason": reason},
        )
        AuditEvent.objects.create(
            actor=request.user,
            action="TEACHER_DECISION",
            entity_type="RecommendationItem",
            entity_id=str(item.id),
            payload={"decision": decision, "overrode_recommendation": decision != item.recommendation},
        )
        Notification.objects.create(
            recipient=submission.owner,
            submission=submission,
            event_type="TEACHER_DECISION",
            message=f"Giáo viên đã gửi kết quả xét hồ sơ {submission.student.full_name}.",
        )
        if not RecommendationItem.objects.filter(run=active_run, teacher_decision__isnull=True).exists():
            submission.status = "COMPLETED"
            submission.save(update_fields=["status", "updated_at"])
        return Response({"data": {"id": str(final.id), "decision": final.decision, "reason": final.reason}})
