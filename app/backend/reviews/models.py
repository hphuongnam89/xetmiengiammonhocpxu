import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    SALES = "SALES", "Sales"
    TEACHER = "TEACHER", "Teacher"


class SubmissionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    IN_REVIEW = "IN_REVIEW", "In review"
    TEACHER_REVIEW = "TEACHER_REVIEW", "Teacher review"
    COMPLETED = "COMPLETED", "Completed"
    REJECTED = "REJECTED", "Rejected"


class RuleStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    APPROVED = "APPROVED", "Approved"
    RETIRED = "RETIRED", "Retired"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=Role.choices)


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_code = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=255)
    program_code = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="submissions")
    teacher = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assigned_submissions",
    )
    status = models.CharField(max_length=30, choices=SubmissionStatus.choices, default=SubmissionStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT, related_name="documents")
    document_type = models.CharField(max_length=50)
    storage_key = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    mime_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("submission", "sha256"), name="uniq_submission_document_hash")]


class RuleVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_code = models.CharField(max_length=100)
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=RuleStatus.choices, default=RuleStatus.DRAFT)
    definition = models.JSONField(default=dict)
    source_reference = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_exemption_rules")
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("rule_code", "version"), name="uniq_rule_version")]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous and previous.status == RuleStatus.APPROVED:
                frozen = ("rule_code", "version", "definition", "source_reference")
                if any(getattr(previous, field) != getattr(self, field) for field in frozen):
                    raise ValidationError("Approved rule versions are immutable. Create a new draft version.")
                if self.status not in {RuleStatus.APPROVED, RuleStatus.RETIRED}:
                    raise ValidationError("Approved rules may only remain approved or be retired.")
        super().save(*args, **kwargs)


class MappingStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    APPROVED = "APPROVED", "Approved"
    RETIRED = "RETIRED", "Retired"


class RuleMappingVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mapping_code = models.CharField(max_length=100)
    version = models.PositiveIntegerField(default=1)
    source_course = models.CharField(max_length=255)
    target_course_code = models.CharField(max_length=100)
    mapping_data = models.JSONField(default=dict)
    source_reference = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=MappingStatus.choices, default=MappingStatus.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_rule_mappings")
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_rule_mappings")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("mapping_code", "version"), name="uniq_mapping_version")]
        ordering = ("mapping_code", "-version")

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous and previous.status == MappingStatus.APPROVED:
                protected = ("mapping_code", "version", "source_course", "target_course_code", "mapping_data", "source_reference")
                if any(getattr(previous, field) != getattr(self, field) for field in protected):
                    raise ValueError("Approved mapping versions are immutable; create a new version.")
        super().save(*args, **kwargs)


class CurriculumVersionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    APPROVED = "APPROVED", "Approved"
    RETIRED = "RETIRED", "Retired"


class Program(models.Model):
    code = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)


class CurriculumVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="curricula")
    version_label = models.CharField(max_length=255)
    source_file = models.CharField(max_length=500)
    source_sha256 = models.CharField(max_length=64)
    source_sheet = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=CurriculumVersionStatus.choices, default=CurriculumVersionStatus.DRAFT)
    imported_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("source_sha256", "source_sheet"), name="uniq_curriculum_source_sheet")]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous and previous.status == CurriculumVersionStatus.APPROVED:
                frozen = ("program_id", "version_label", "source_file", "source_sha256", "source_sheet")
                if any(getattr(previous, field) != getattr(self, field) for field in frozen):
                    raise ValueError("Approved curriculum versions are immutable.")
        super().save(*args, **kwargs)


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(CurriculumVersion, on_delete=models.PROTECT, related_name="courses")
    raw_code = models.CharField(max_length=100, blank=True)
    raw_name = models.CharField(max_length=500)
    credits = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    course_type = models.CharField(max_length=100, blank=True)
    assessment = models.CharField(max_length=255, blank=True)
    source_row = models.PositiveIntegerField()
    source_cells = models.JSONField(default=dict)
    review_status = models.CharField(max_length=20, default="PENDING")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("curriculum", "source_row"), name="uniq_curriculum_source_row")]

    def save(self, *args, **kwargs):
        if self.curriculum_id and self.curriculum.status == CurriculumVersionStatus.APPROVED:
            if self.pk:
                previous = type(self).objects.filter(pk=self.pk).first()
                if previous and any(getattr(previous, field) != getattr(self, field) for field in
                                    ("raw_code", "raw_name", "credits", "course_type", "assessment", "source_cells")):
                    raise ValueError("Courses in an approved curriculum are immutable.")
            elif self.pk is None:
                raise ValueError("Cannot add courses to an approved curriculum.")
        super().save(*args, **kwargs)


class HistoricalDecisionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
    APPROVED = "APPROVED", "Approved precedent"
    REJECTED = "REJECTED", "Rejected"


class HistoricalDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_sha256 = models.CharField(max_length=64)
    source_file = models.CharField(max_length=500)
    source_sheet = models.CharField(max_length=255)
    source_row = models.PositiveIntegerField()
    source_key_hash = models.CharField(max_length=64, blank=True)
    program_code = models.CharField(max_length=100, blank=True)
    course_code = models.CharField(max_length=100, blank=True)
    course_name = models.CharField(max_length=500, blank=True)
    decision_raw = models.CharField(max_length=255, blank=True)
    decision = models.CharField(max_length=30, blank=True)
    source_cells = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=HistoricalDecisionStatus.choices, default=HistoricalDecisionStatus.PENDING)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("source_sha256", "source_sheet", "source_row"), name="uniq_historical_source_row")]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous and previous.status == HistoricalDecisionStatus.APPROVED:
                frozen = ("source_sha256", "source_file", "source_sheet", "source_row", "source_key_hash", "program_code",
                          "course_code", "course_name", "decision_raw", "decision", "source_cells")
                if any(getattr(previous, field) != getattr(self, field) for field in frozen):
                    raise ValueError("Approved historical precedents are immutable.")
        super().save(*args, **kwargs)


class RecommendationRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT, related_name="recommendation_runs")
    rule_version = models.ForeignKey(RuleVersion, on_delete=models.PROTECT)
    curriculum_version = models.ForeignKey(CurriculumVersion, on_delete=models.PROTECT, null=True, blank=True)
    provider = models.CharField(max_length=50, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, default="PENDING")
    is_current = models.BooleanField(default=False)
    prompt_hash = models.CharField(max_length=64, blank=True)
    idempotency_key = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("submission", "idempotency_key"), name="uniq_submission_recommendation_key"),
            models.UniqueConstraint(fields=("submission",), condition=models.Q(is_current=True), name="uniq_current_recommendation_run"),
        ]

    def clean(self):
        if self.rule_version_id and self.rule_version.status != RuleStatus.APPROVED:
            raise ValidationError("Only approved rule versions can run in production.")


class RecommendationItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(RecommendationRun, on_delete=models.PROTECT, related_name="items")
    course_code = models.CharField(max_length=100)
    recommendation = models.CharField(max_length=30)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    rationale = models.TextField(blank=True)
    evidence = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class TeacherDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.OneToOneField(RecommendationItem, on_delete=models.PROTECT, related_name="teacher_decision")
    teacher = models.ForeignKey(User, on_delete=models.PROTECT)
    decision = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class AIUsageEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(RecommendationRun, null=True, blank=True, on_delete=models.PROTECT)
    provider = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    operation = models.CharField(max_length=100)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    request_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="notifications")
    submission = models.ForeignKey(Submission, null=True, blank=True, on_delete=models.PROTECT)
    event_type = models.CharField(max_length=50)
    message = models.CharField(max_length=500)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ExtractionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
    NEEDS_REVIEW = "NEEDS_REVIEW", "Needs review"
    FAILED = "FAILED", "Failed"


class FieldReviewStatus(models.TextChoices):
    AUTO_ACCEPTED = "AUTO_ACCEPTED", "Auto accepted"
    HUMAN_ACCEPTED = "HUMAN_ACCEPTED", "Human accepted"
    NEEDS_REVIEW = "NEEDS_REVIEW", "Needs review"
    REJECTED = "REJECTED", "Rejected"


class ExtractionRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT, related_name="extraction_runs")
    engine = models.CharField(max_length=100)
    model_version = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=ExtractionStatus.choices, default=ExtractionStatus.PENDING)
    raw_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ExtractedField(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(ExtractionRun, on_delete=models.PROTECT, related_name="fields")
    field_key = models.CharField(max_length=100)
    raw_value = models.TextField(blank=True)
    normalized_value = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    evidence_text = models.TextField(blank=True)
    bounding_box = models.JSONField(null=True, blank=True)
    review_status = models.CharField(max_length=30, choices=FieldReviewStatus.choices, default=FieldReviewStatus.NEEDS_REVIEW)
    created_at = models.DateTimeField(auto_now_add=True)


class ExtractedCourseRow(models.Model):
    """An explicitly assembled course row; fields are never grouped heuristically."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT, related_name="extracted_course_rows")
    source_course_name = models.ForeignKey(ExtractedField, on_delete=models.PROTECT, related_name="course_rows_as_name")
    source_course_code = models.ForeignKey(ExtractedField, null=True, blank=True, on_delete=models.PROTECT, related_name="course_rows_as_code")
    prior_grade = models.ForeignKey(ExtractedField, on_delete=models.PROTECT, related_name="course_rows_as_grade")
    prior_credits = models.ForeignKey(ExtractedField, on_delete=models.PROTECT, related_name="course_rows_as_credits")
    target_course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="evidence_rows")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=("submission", "source_course_name", "prior_grade", "prior_credits", "target_course"),
            name="uniq_submission_course_evidence_row",
        )]
