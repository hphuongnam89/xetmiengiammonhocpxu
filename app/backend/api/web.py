from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
import hashlib
import uuid
from pathlib import Path

from reviews.models import (
    AuditEvent,
    Notification,
    RecommendationItem,
    Role,
    Submission,
    SubmissionStatus,
    TeacherDecision,
    DocumentVersion,
    Student,
    UserProfile,
    ExtractedField,
    ExtractionRun,
    FieldReviewStatus,
    Course,
    CurriculumVersion,
    CurriculumVersionStatus,
    ExtractedCourseRow,
    RuleStatus,
    RuleVersion,
)

from .permissions import user_role


@login_required
def dashboard(request):
    role = user_role(request.user)
    context = {"role": role, "notifications": Notification.objects.filter(recipient=request.user)[:10]}
    if role == Role.SALES:
        context["submissions"] = Submission.objects.filter(owner=request.user).select_related("student", "teacher")
    elif role == Role.TEACHER:
        context["submissions"] = Submission.objects.filter(teacher=request.user).select_related("student", "owner")
    elif role == Role.ADMIN:
        context["submissions"] = Submission.objects.select_related("student", "owner", "teacher")[:100]
    else:
        messages.error(request, "Tài khoản chưa được phân quyền.")
        context["submissions"] = []
    return render(request, "reviews/dashboard.html", context)


@login_required
def create_submission(request):
    if user_role(request.user) not in {Role.SALES, Role.ADMIN}:
        return HttpResponseForbidden("Không có quyền tạo hồ sơ.")
    teachers = UserProfile.objects.filter(role=Role.TEACHER).select_related("user")
    if request.method == "POST":
        code = request.POST.get("student_code", "").strip()[:100]
        name = request.POST.get("full_name", "").strip()[:255]
        program = request.POST.get("program_code", "").strip()[:100]
        teacher_id = request.POST.get("teacher_id") or None
        uploaded = request.FILES.get("file")
        if not code or not name or not uploaded:
            messages.error(request, "Nhập mã, họ tên và tải lên bảng điểm/văn bằng.")
        else:
            ext = Path(uploaded.name).suffix.lower()
            allowed = {".pdf": ("application/pdf", b"%PDF-"), ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
                       ".jpeg": ("image/jpeg", b"\xff\xd8\xff"), ".png": ("image/png", b"\x89PNG\r\n\x1a\n")}
            expected = allowed.get(ext)
            head = uploaded.read(8)
            uploaded.seek(0)
            if uploaded.size > 10 * 1024 * 1024 or not expected or uploaded.content_type != expected[0] or not head.startswith(expected[1]):
                messages.error(request, "File phải là PDF/JPG/PNG hợp lệ và không quá 10 MB.")
            elif teacher_id and not UserProfile.objects.filter(user_id=teacher_id, role=Role.TEACHER).exists():
                messages.error(request, "Giáo viên được chọn không hợp lệ.")
            else:
                try:
                    student, _ = Student.objects.get_or_create(
                        student_code=code, defaults={"full_name": name, "program_code": program}
                    )
                    submission = Submission.objects.create(student=student, owner=request.user, teacher_id=teacher_id)
                    digest = hashlib.sha256()
                    for chunk in uploaded.chunks():
                        digest.update(chunk)
                    uploaded.seek(0)
                    key = f"documents/{submission.id}/{uuid.uuid4()}{ext}"
                    default_storage.save(key, uploaded)
                    DocumentVersion.objects.create(
                        submission=submission,
                        document_type=request.POST.get("document_type", "TRANSCRIPT")[:50],
                        storage_key=key,
                        sha256=digest.hexdigest(),
                        mime_type=expected[0],
                    )
                    if submission.teacher_id:
                        Notification.objects.create(recipient=submission.teacher, submission=submission,
                            event_type="SUBMISSION_ASSIGNED", message=f"Bạn được phân công xét hồ sơ {student.full_name}.")
                    messages.success(request, "Đã tạo hồ sơ và tải tài liệu.")
                    return redirect("dashboard")
                except Exception:
                    messages.error(request, "Không thể tạo hồ sơ. Kiểm tra mã sinh viên và thử lại.")
    return render(request, "reviews/submission_form.html", {"teachers": teachers})


@login_required
def upload_submission_document(request, submission_id):
    if request.method != "POST":
        return HttpResponseForbidden("Chỉ chấp nhận POST.")
    submission = get_object_or_404(Submission, pk=submission_id)
    role = user_role(request.user)
    if role != Role.ADMIN and not (role == Role.SALES and submission.owner_id == request.user.id):
        return HttpResponseForbidden("Bạn không có quyền tải tài liệu vào hồ sơ này.")
    uploaded = request.FILES.get("file")
    ext = Path(uploaded.name).suffix.lower() if uploaded else ""
    allowed = {".pdf": ("application/pdf", b"%PDF-"), ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
               ".jpeg": ("image/jpeg", b"\xff\xd8\xff"), ".png": ("image/png", b"\x89PNG\r\n\x1a\n")}
    expected = allowed.get(ext)
    head = uploaded.read(8) if uploaded else b""
    if uploaded:
        uploaded.seek(0)
    if not uploaded or uploaded.size > 10 * 1024 * 1024 or not expected or uploaded.content_type != expected[0] or not head.startswith(expected[1]):
        messages.error(request, "File không hợp lệ. Chỉ nhận PDF/JPG/PNG tối đa 10 MB.")
        return redirect("dashboard")
    digest = hashlib.sha256()
    for chunk in uploaded.chunks():
        digest.update(chunk)
    uploaded.seek(0)
    key = f"documents/{submission.id}/{uuid.uuid4()}{ext}"
    default_storage.save(key, uploaded)
    DocumentVersion.objects.create(
        submission=submission,
        document_type=request.POST.get("document_type", "OTHER")[:50],
        storage_key=key,
        sha256=digest.hexdigest(),
        mime_type=expected[0],
    )
    messages.success(request, "Đã thêm tài liệu vào hồ sơ.")
    return redirect("dashboard")


@login_required
def mark_notification_read(request, notification_id):
    if request.method != "POST":
        return HttpResponseForbidden("Chỉ chấp nhận POST.")
    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    if notification.read_at is None:
        from django.utils import timezone
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("dashboard")


@login_required
def review_submission(request, submission_id):
    role = user_role(request.user)
    submission = get_object_or_404(Submission.objects.select_related("student", "owner", "teacher"), pk=submission_id)
    can_review = role == Role.ADMIN or (role == Role.TEACHER and submission.teacher_id == request.user.id)
    can_create = role == Role.ADMIN or (role == Role.SALES and submission.owner_id == request.user.id)
    if not (can_review or can_create):
        messages.error(request, "Bạn không có quyền xem hồ sơ này.")
        return redirect("dashboard")
    current_run = submission.recommendation_runs.filter(is_current=True).select_related("rule_version", "curriculum_version").first()
    items = RecommendationItem.objects.filter(run=current_run).select_related("run").prefetch_related("teacher_decision") if current_run else RecommendationItem.objects.none()
    if request.method == "POST":
        if request.POST.get("action") == "create_recommendation":
            if not can_create:
                return HttpResponseForbidden("Chỉ Sales phụ trách hoặc Admin được tạo đề xuất.")
            from .recommendation_service import RecommendationInputError, create_recommendation_run
            try:
                rule = RuleVersion.objects.get(pk=request.POST.get("rule_version_id"), status=RuleStatus.APPROVED)
                curriculum = CurriculumVersion.objects.get(pk=request.POST.get("curriculum_version_id"))
                run, created = create_recommendation_run(
                    submission=submission, actor=request.user, rule=rule, curriculum=curriculum,
                    course_row_ids=request.POST.getlist("course_row_ids"),
                    idempotency_key=request.POST.get("idempotency_key", "").strip(),
                )
            except (RuleVersion.DoesNotExist, CurriculumVersion.DoesNotExist, ValidationError, ValueError, TypeError) as exc:
                messages.error(request, str(exc) or "Chưa chọn rule và chương trình hợp lệ.")
            else:
                messages.success(request, "Đề xuất đã được tạo." if created else "Đề xuất này đã được tạo trước đó.")
                return redirect("review-submission", submission_id=submission.id)
        elif request.POST.get("action") == "teacher_decision":
            if not can_review:
                return HttpResponseForbidden("Chỉ giảng viên được giao hoặc Admin được ghi quyết định.")
            item = get_object_or_404(items, pk=request.POST.get("item_id"))
            decision = request.POST.get("decision", "")
            reason = request.POST.get("reason", "").strip()
            if decision not in {"FULL", "PARTIAL", "NOT_ELIGIBLE"}:
                messages.error(request, "Lựa chọn quyết định không hợp lệ.")
            elif decision != item.recommendation and not reason:
                messages.error(request, "Cần ghi lý do khi điều chỉnh đề xuất AI.")
            else:
                TeacherDecision.objects.update_or_create(
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
                    message=f"Giáo viên đã cập nhật kết quả môn {item.course_code}.",
                )
                if not items.filter(teacher_decision__isnull=True).exists():
                    submission.status = SubmissionStatus.COMPLETED
                    submission.save(update_fields=["status", "updated_at"])
                messages.success(request, "Đã lưu quyết định môn học.")
                return redirect("review-submission", submission_id=submission.id)
        else:
            return HttpResponseForbidden("Thao tác không hợp lệ.")
    documents = DocumentVersion.objects.filter(submission=submission)
    rows = ExtractedCourseRow.objects.filter(submission=submission).select_related(
        "source_course_name__run__document", "prior_grade", "prior_credits",
        "target_course__curriculum", "target_course__curriculum__program")
    curricula = CurriculumVersion.objects.filter(status=CurriculumVersionStatus.APPROVED).select_related("program")
    if submission.student.program_code:
        curricula = curricula.filter(program_id__iexact=submission.student.program_code)
    rules = []
    for rule in RuleVersion.objects.filter(status=RuleStatus.APPROVED):
        definition = rule.definition if isinstance(rule.definition, dict) else {}
        review = definition.get("academic_owner_review") or {}
        if (isinstance(review, dict) and isinstance(definition.get("rules"), list) and definition.get("rules")
                and review.get("verified") is True and review.get("reviewer") and review.get("note")):
            rules.append(rule)
    return render(request, "reviews/review.html", {
        "submission": submission, "items": items, "documents": documents, "role": role,
        "current_run": current_run, "rows": rows, "curricula": curricula, "rules": rules,
        "can_create_recommendation": can_create,
        "idempotency_key": uuid.uuid4(),
    })


def _can_access_document(user, document):
    role = user_role(user)
    return role == Role.ADMIN or (role == Role.SALES and document.submission.owner_id == user.id) or (
        role == Role.TEACHER and document.submission.teacher_id == user.id
    )


@login_required
def view_document(request, document_id):
    document = get_object_or_404(DocumentVersion.objects.select_related("submission"), pk=document_id)
    if not _can_access_document(request.user, document):
        return HttpResponseForbidden("Bạn không có quyền xem tài liệu này.")
    response = FileResponse(
        default_storage.open(document.storage_key, "rb"),
        content_type=document.mime_type,
        filename=f"{document.id}",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def review_extraction(request, document_id):
    document = get_object_or_404(DocumentVersion.objects.select_related("submission"), pk=document_id)
    if not _can_access_document(request.user, document):
        return HttpResponseForbidden("Bạn không có quyền xem tài liệu này.")
    role = user_role(request.user)
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "extract":
            if role not in {Role.ADMIN, Role.SALES}:
                return HttpResponseForbidden("Chỉ Sales phụ trách hoặc Admin được chạy OCR.")
            if role == Role.SALES and document.submission.owner_id != request.user.id:
                return HttpResponseForbidden("Bạn không có quyền chạy OCR cho hồ sơ này.")
            from .extraction import extract_document
            extract_document(document)
            messages.success(request, "Đã tạo bản trích xuất. Các trường vẫn cần người kiểm tra.")
            return redirect("review-extraction", document_id=document.id)
        elif action == "review_field":
            if role not in {Role.ADMIN, Role.TEACHER}:
                return HttpResponseForbidden("Chỉ giáo viên phụ trách hoặc Admin được xác nhận trường OCR.")
            field = get_object_or_404(ExtractedField.objects.select_related("run__document"),
                                      pk=request.POST.get("field_id"), run__document=document)
            status = request.POST.get("review_status", "")
            normalized = request.POST.get("normalized_value", "").strip()
            valid_statuses = {choice for choice, _label in FieldReviewStatus.choices}
            if status not in valid_statuses or len(normalized) > 1000:
                messages.error(request, "Trạng thái hoặc nội dung hiệu chỉnh không hợp lệ.")
            elif status in {FieldReviewStatus.AUTO_ACCEPTED, FieldReviewStatus.HUMAN_ACCEPTED} and not normalized:
                messages.error(request, "Trường được xác nhận phải có giá trị đã kiểm tra.")
            else:
                previous_status = field.review_status
                normalized_changed = field.normalized_value != normalized
                field.normalized_value = normalized
                field.review_status = status
                field.save(update_fields=["normalized_value", "review_status"])
                AuditEvent.objects.create(
                    actor=request.user,
                    action="EXTRACTED_FIELD_REVIEWED",
                    entity_type="ExtractedField",
                    entity_id=str(field.id),
                    payload={"field_key": field.field_key, "previous_status": previous_status,
                             "review_status": status, "normalized_value_changed": normalized_changed},
                )
                messages.success(request, "Đã lưu trạng thái kiểm tra. Bản OCR gốc được giữ nguyên.")
                return redirect("review-extraction", document_id=document.id)
        elif action == "add_field":
            if role not in {Role.ADMIN, Role.TEACHER}:
                return HttpResponseForbidden("Chỉ giáo viên phụ trách hoặc Admin được bổ sung trường.")
            field_key = request.POST.get("field_key", "")
            normalized = request.POST.get("normalized_value", "").strip()
            evidence = request.POST.get("evidence_text", "").strip()
            raw_page = request.POST.get("page_number", "").strip()
            allowed_fields = {"student_name", "school_name", "program", "course_name", "course_code", "credits", "grade", "document_date"}
            run = ExtractionRun.objects.filter(document=document).order_by("-created_at").first()
            try:
                page_number = int(raw_page) if raw_page else None
            except ValueError:
                page_number = 0
            if (field_key not in allowed_fields or not normalized or len(normalized) > 1000
                    or len(evidence) > 2000 or (page_number is not None and not 1 <= page_number <= 10000)):
                messages.error(request, "Trường bổ sung, giá trị, trang hoặc bằng chứng không hợp lệ.")
            elif run is None:
                messages.error(request, "Chạy OCR trước khi bổ sung trường.")
            else:
                field = ExtractedField.objects.create(
                    run=run, field_key=field_key, raw_value="", normalized_value=normalized,
                    evidence_text=evidence, page_number=page_number,
                    review_status=FieldReviewStatus.HUMAN_ACCEPTED,
                )
                AuditEvent.objects.create(
                    actor=request.user, action="EXTRACTED_FIELD_ADDED_BY_TEACHER",
                    entity_type="ExtractedField", entity_id=str(field.id),
                    payload={"field_key": field_key, "page_number": page_number,
                             "evidence_provided": bool(evidence)},
                )
                messages.success(request, "Đã thêm trường do giáo viên đối chiếu từ tài liệu gốc.")
                return redirect("review-extraction", document_id=document.id)
        elif action == "assemble_course_row":
            if role not in {Role.ADMIN, Role.TEACHER}:
                return HttpResponseForbidden("Chỉ giáo viên phụ trách hoặc Admin được ghép dòng môn học.")
            from .recommendation_service import RecommendationInputError, create_course_row
            try:
                name_field = ExtractedField.objects.select_related("run__document").get(
                    pk=request.POST.get("course_name_field"), run__document=document)
                grade_field = ExtractedField.objects.select_related("run__document").get(
                    pk=request.POST.get("grade_field"), run__document=document)
                credits_field = ExtractedField.objects.select_related("run__document").get(
                    pk=request.POST.get("credits_field"), run__document=document)
                code_id = request.POST.get("course_code_field", "").strip()
                code_field = ExtractedField.objects.select_related("run__document").get(
                    pk=code_id, run__document=document) if code_id else None
                target_course = Course.objects.select_related("curriculum").get(pk=request.POST.get("target_course"))
            except (ExtractedField.DoesNotExist, Course.DoesNotExist, ValidationError, ValueError, TypeError):
                messages.error(request, "Chọn các trường OCR và môn đích hợp lệ.")
            else:
                try:
                    row = create_course_row(
                        submission=document.submission, actor=request.user,
                        name_field=name_field, grade_field=grade_field,
                        credits_field=credits_field, code_field=code_field,
                        target_course=target_course,
                    )
                except RecommendationInputError as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(request, f"Đã lưu dòng môn học đã đối chiếu ({row.target_course.raw_code}).")
                    return redirect("review-extraction", document_id=document.id)
        else:
            return HttpResponseForbidden("Thao tác không hợp lệ.")
    runs = ExtractionRun.objects.filter(document=document).prefetch_related("fields").order_by("-created_at")
    latest_run = runs.first()
    confirmed = latest_run.fields.filter(review_status=FieldReviewStatus.HUMAN_ACCEPTED) if latest_run else ExtractedField.objects.none()
    program_code = document.submission.student.program_code
    target_courses = Course.objects.filter(
        curriculum__status=CurriculumVersionStatus.APPROVED,
        review_status="APPROVED",
        raw_code__gt="",
    ).select_related("curriculum", "curriculum__program")
    if program_code:
        target_courses = target_courses.filter(curriculum__program_id__iexact=program_code)
    existing_rows = ExtractedCourseRow.objects.filter(submission=document.submission).select_related(
        "source_course_name__run__document", "target_course", "target_course__curriculum")
    return render(request, "reviews/extraction_review.html", {
        "document": document, "runs": runs, "role": role, "latest_run": latest_run,
        "confirmed_course_names": confirmed.filter(field_key="course_name"),
        "confirmed_course_codes": confirmed.filter(field_key="course_code"),
        "confirmed_grades": confirmed.filter(field_key="grade"),
        "confirmed_credits": confirmed.filter(field_key="credits"),
        "target_courses": target_courses,
        "existing_rows": existing_rows,
    })
