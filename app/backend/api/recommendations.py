from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import (
    AuditEvent,
    MappingStatus,
    RuleMappingVersion,
    HistoricalDecision,
    HistoricalDecisionStatus,
    RecommendationItem,
    RecommendationRun,
    Role,
    RuleStatus,
    RuleVersion,
    Submission,
    SubmissionStatus,
    TeacherDecision,
    Notification,
)

from .permissions import user_role
from .rule_engine import evaluate_course


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
        rule = get_object_or_404(RuleVersion, pk=request.data.get("rule_version_id"))
        if rule.status != RuleStatus.APPROVED:
            return Response({"error": {"code": "rule_not_approved", "message": "Rule version is not approved."}}, status=422)
        key = str(request.data.get("idempotency_key", "")).strip()[:100]
        if not key:
            return Response({"error": {"code": "idempotency_key_required", "message": "Idempotency key is required."}}, status=422)
        existing = RecommendationRun.objects.filter(submission=submission, idempotency_key=key).prefetch_related("items").first()
        if existing:
            return Response({"data": self._serialize(existing)}, status=200)
        items = request.data.get("items")
        if not isinstance(items, list) or not items:
            return Response({"error": {"code": "items_required", "message": "At least one course item is required."}}, status=422)
        with transaction.atomic():
            run = RecommendationRun.objects.create(
                submission=submission,
                rule_version=rule,
                provider="deterministic",
                model_name="rule-engine-v1",
                status="COMPLETED",
                idempotency_key=key,
            )
            for item in items:
                course_code = str(item.get("course_code", "")).strip()[:100]
                prior_course = str(item.get("prior_course", "")).strip()[:255]
                mapping = None
                if course_code and prior_course:
                    mapping = RuleMappingVersion.objects.filter(
                        target_course_code__iexact=course_code,
                        source_course__iexact=prior_course,
                        status=MappingStatus.APPROVED,
                    ).order_by("-version").first()
                evidence = item.get("evidence", [])
                evidence = evidence if isinstance(evidence, list) else []
                if mapping:
                    evidence = [*evidence, f"approved_mapping:{mapping.mapping_code}:v{mapping.version}:{mapping.source_reference}"]
                decision = evaluate_course(
                    course_code=course_code,
                    rule_approved=True,
                    prior_grade=item.get("prior_grade"),
                    prior_credits=item.get("prior_credits"),
                    content_match=True if mapping else None,
                    evidence=evidence,
                )
                program_code = submission.student.program_code
                if program_code:
                    precedent_counts = list(HistoricalDecision.objects.filter(
                        program_code__iexact=program_code,
                        course_code__iexact=course_code,
                        status=HistoricalDecisionStatus.APPROVED,
                    ).values("decision").annotate(total=Count("id")).order_by("decision"))
                    if precedent_counts:
                        context = ",".join(f"{row['decision']}={row['total']}" for row in precedent_counts)
                        decision = type(decision)(decision.course_code, decision.recommendation,
                            decision.evidence + (f"approved_history_context:{context}; context only",),
                            decision.reason + " Historical approved outcomes are context only and did not change this result.",
                            decision.confidence, decision.needs_human_review)
                RecommendationItem.objects.create(
                    run=run,
                    course_code=decision.course_code,
                    recommendation=decision.recommendation,
                    confidence=decision.confidence,
                    rationale=decision.reason,
                    evidence=list(decision.evidence),
                )
            submission.status = SubmissionStatus.TEACHER_REVIEW
            submission.save(update_fields=["status", "updated_at"])
            if submission.teacher_id:
                Notification.objects.create(
                    recipient=submission.teacher,
                    submission=submission,
                    event_type="RECOMMENDATION_READY",
                    message=f"Đề xuất miễn môn đã sẵn sàng: {submission.student.full_name}.",
                )
        return Response({"data": self._serialize(run)}, status=201)

    @staticmethod
    def _serialize(run):
        return {
            "id": str(run.id),
            "status": run.status,
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
        if not RecommendationItem.objects.filter(run=item.run, teacher_decision__isnull=True).exists():
            submission.status = SubmissionStatus.COMPLETED
            submission.save(update_fields=["status", "updated_at"])
        return Response({"data": {"id": str(final.id), "decision": final.decision, "reason": final.reason}})
