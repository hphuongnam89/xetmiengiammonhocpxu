import hashlib
import json
from decimal import Decimal, InvalidOperation
from django.db.models import Q

from django.db import transaction

from reviews.models import (
    AuditEvent,
    CurriculumVersionStatus,
    ExtractedCourseRow,
    FieldReviewStatus,
    MappingStatus,
    Notification,
    RecommendationItem,
    RecommendationRun,
    RuleMappingVersion,
    RuleStatus,
    Submission,
    SubmissionStatus,
)

from .rule_engine import CourseDecision, evaluate_course


class RecommendationInputError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _confirmed_value(field, expected_key):
    if field.field_key != expected_key or field.review_status != FieldReviewStatus.HUMAN_ACCEPTED:
        raise RecommendationInputError("field_not_confirmed", "Only teacher-confirmed fields can be used.")
    value = field.normalized_value.strip()
    if not value:
        raise RecommendationInputError("field_value_missing", "A confirmed field has no normalized value.")
    return value


def _numeric_value(field, expected_key):
    value = _confirmed_value(field, expected_key).replace(",", ".")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise RecommendationInputError("invalid_academic_value", "Grade and credits must be numeric.") from exc
    if not number.is_finite():
        raise RecommendationInputError("invalid_academic_value", "Grade and credits must be finite numbers.")
    return number


@transaction.atomic
def create_course_row(*, submission, actor, name_field, grade_field, credits_field, code_field, target_course):
    fields = [name_field, grade_field, credits_field, *([code_field] if code_field else [])]
    for field in fields:
        if field.run.document.submission_id != submission.id:
            raise RecommendationInputError("field_submission_mismatch", "All source fields must belong to this submission.")
        if not field.evidence_text.strip() and field.page_number is None:
            raise RecommendationInputError("field_evidence_missing", "Each selected field needs source text or a source page.")
    if len({field.run_id for field in fields}) != 1:
        raise RecommendationInputError("field_run_mismatch", "All source fields must come from the same extraction run.")
    name = _confirmed_value(name_field, "course_name")
    _numeric_value(grade_field, "grade")
    _numeric_value(credits_field, "credits")
    if code_field:
        _confirmed_value(code_field, "course_code")
    if (target_course.curriculum.status != CurriculumVersionStatus.APPROVED
            or target_course.review_status != "APPROVED" or not target_course.raw_code.strip()):
        raise RecommendationInputError("target_course_unavailable", "Choose a coded course from an approved curriculum.")
    if (submission.student.program_code and
            submission.student.program_code.casefold() != target_course.curriculum.program_id.casefold()):
        raise RecommendationInputError("curriculum_program_mismatch", "Môn đích không thuộc chương trình của hồ sơ sinh viên.")
    row, created = ExtractedCourseRow.objects.get_or_create(
        submission=submission,
        source_course_name=name_field,
        prior_grade=grade_field,
        prior_credits=credits_field,
        target_course=target_course,
        defaults={"source_course_code": code_field, "created_by": actor},
    )
    if not created and row.source_course_code_id != (code_field.id if code_field else None):
        raise RecommendationInputError("course_row_conflict", "Dòng này đã được ghép với mã môn nguồn khác.")
    if created:
        AuditEvent.objects.create(
            actor=actor,
            action="EXTRACTED_COURSE_ROW_ASSEMBLED",
            entity_type="ExtractedCourseRow",
            entity_id=str(row.id),
            payload={"field_ids": [str(field.id) for field in fields], "target_course_id": str(target_course.id)},
        )
    return row


def _evidence(field, label):
    return {
        "kind": "confirmed_extracted_field",
        "label": label,
        "review_status": field.review_status,
        "field_id": str(field.id),
        "document_id": str(field.run.document_id),
        "document_sha256": field.run.document.sha256,
        "extraction_run_id": str(field.run_id),
        "page_number": field.page_number,
        "value": field.normalized_value,
        "source_value": field.raw_value,
        "evidence_text": field.evidence_text,
    }


@transaction.atomic
def create_recommendation_run(*, submission, actor, rule, curriculum, course_row_ids, idempotency_key):
    if not idempotency_key or len(idempotency_key) > 100:
        raise RecommendationInputError("idempotency_key_required", "Mã chống tạo trùng không hợp lệ.")
    if not course_row_ids or len(course_row_ids) > 500 or len(set(course_row_ids)) != len(course_row_ids):
        raise RecommendationInputError("course_rows_required", "Chọn ít nhất một dòng môn học khác nhau.")
    key_payload = {"rule": str(rule.id), "curriculum": str(curriculum.id), "rows": sorted(map(str, course_row_ids))}
    key_hash = hashlib.sha256(json.dumps(key_payload, sort_keys=True).encode()).hexdigest()
    existing = RecommendationRun.objects.filter(submission=submission, idempotency_key=idempotency_key).first()
    if existing:
        if existing.prompt_hash and existing.prompt_hash != key_hash:
            raise RecommendationInputError("idempotency_key_conflict", "Mã chống tạo trùng này đã được dùng cho dữ liệu khác.")
        return existing, False
    if rule.status != RuleStatus.APPROVED:
        raise RecommendationInputError("rule_not_approved", "Chưa có phiên bản quy tắc đã duyệt.")
    definition = rule.definition if isinstance(rule.definition, dict) else {}
    review = definition.get("academic_owner_review") or {}
    if not isinstance(review, dict):
        review = {}
    if (not definition.get("rules") or not isinstance(definition.get("rules"), list)
            or review.get("verified") is not True
            or not review.get("reviewer")
            or not review.get("note")):
        raise RecommendationInputError("rule_not_ready", "Quy tắc thiếu nội dung hoặc xác nhận của chủ học thuật.")
    if curriculum.status != CurriculumVersionStatus.APPROVED:
        raise RecommendationInputError("curriculum_not_approved", "Chương trình đích chưa được duyệt.")
    if submission.student.program_code and submission.student.program_code.casefold() != curriculum.program_id.casefold():
        raise RecommendationInputError("curriculum_program_mismatch", "Chương trình đích không khớp hồ sơ sinh viên.")
    rows = list(
        ExtractedCourseRow.objects.filter(submission=submission, pk__in=course_row_ids)
        .select_related("source_course_name__run__document", "source_course_code__run__document",
                        "prior_grade__run__document", "prior_credits__run__document",
                        "target_course__curriculum")
    )
    if len(rows) != len(course_row_ids):
        raise RecommendationInputError("course_rows_unavailable", "Một số dòng môn học không thuộc hồ sơ này.")
    if any(row.target_course.curriculum_id != curriculum.id for row in rows):
        raise RecommendationInputError("target_curriculum_mismatch", "Các dòng môn học không cùng curriculum đã chọn.")

    RecommendationRun.objects.filter(submission=submission, is_current=True).update(is_current=False)
    run = RecommendationRun.objects.create(
        submission=submission,
        rule_version=rule,
        curriculum_version=curriculum,
        provider="deterministic",
        model_name="rule-engine-v1",
        status="COMPLETED",
        is_current=True,
        idempotency_key=idempotency_key,
        prompt_hash=key_hash,
    )
    for row in rows:
        name = _confirmed_value(row.source_course_name, "course_name")
        grade = _numeric_value(row.prior_grade, "grade")
        credits = _numeric_value(row.prior_credits, "credits")
        target = row.target_course
        if (target.curriculum.status != CurriculumVersionStatus.APPROVED
                or target.review_status != "APPROVED" or not target.raw_code.strip()):
            raise RecommendationInputError("target_course_unavailable", "Môn đích không còn ở curriculum đã duyệt.")
        source_identities = [name]
        if row.source_course_code_id:
            source_identities.append(_confirmed_value(row.source_course_code, "course_code"))
        candidates = RuleMappingVersion.objects.filter(
            target_course_code__iexact=target.raw_code.strip(),
            status=MappingStatus.APPROVED,
        ).filter(Q(source_course__iexact=source_identities[0]) |
                 (Q(source_course__iexact=source_identities[1]) if len(source_identities) > 1 else Q(pk__in=[])))
        verified_mappings = {}
        for candidate in candidates.order_by("-version"):
            review = candidate.mapping_data.get("academic_owner_review", {}) if isinstance(candidate.mapping_data, dict) else {}
            if (review.get("verified") is True and review.get("reviewer") and review.get("note")
                    and candidate.mapping_code not in verified_mappings):
                verified_mappings[candidate.mapping_code] = candidate
        mapping = next(iter(verified_mappings.values())) if len(verified_mappings) == 1 else None
        mapping_ambiguous = len(verified_mappings) > 1
        source_fields = [row.source_course_name, row.prior_grade, row.prior_credits]
        if row.source_course_code_id:
            source_fields.append(row.source_course_code)
        evidence = [_evidence(field, field.field_key) for field in source_fields]
        evidence.append({
            "kind": "approved_target_course",
            "course_id": str(target.id),
            "course_code": target.raw_code,
            "course_name": target.raw_name,
            "curriculum_id": str(curriculum.id),
            "curriculum_program": curriculum.program_id,
            "curriculum_version": curriculum.version_label,
            "curriculum_source": curriculum.source_file,
        })
        if mapping:
            evidence.append({"kind": "approved_mapping", "mapping_code": mapping.mapping_code,
                             "version": mapping.version, "source_reference": mapping.source_reference,
                             "mapping_id": str(mapping.id)})
        elif mapping_ambiguous:
            evidence.append({"kind": "mapping_review_required", "reason": "Multiple approved mappings match the selected source and target."})
        if mapping:
            decision = evaluate_course(
                course_code=target.raw_code.strip(),
                rule_approved=True,
                prior_grade=grade,
                prior_credits=credits,
                content_match=True,
                evidence=evidence,
            )
        else:
            reason = ("Có nhiều mapping học thuật phù hợp; cần giảng viên rà soát." if mapping_ambiguous else
                      "Chưa có mapping học thuật đã duyệt cho môn nguồn này; cần giảng viên rà soát.")
            decision = CourseDecision(target.raw_code.strip(), "NEEDS_HUMAN_REVIEW", tuple(evidence), reason,
                                      Decimal("0"), True)
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
    AuditEvent.objects.create(actor=actor, action="RECOMMENDATION_RUN_CREATED", entity_type="RecommendationRun",
                              entity_id=str(run.id), payload=key_payload)
    return run, True
