from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from .models import (
    DocumentVersion,
    RecommendationRun,
    RuleStatus,
    RuleVersion,
    Student,
    Submission,
)


class DataIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sales-1")
        self.student = Student.objects.create(student_code="SV001", full_name="Nguyen Van A")
        self.submission = Submission.objects.create(student=self.student, owner=self.user)

    def test_document_hash_is_unique_per_submission(self):
        fields = {
            "submission": self.submission,
            "document_type": "TRANSCRIPT",
            "storage_key": "documents/a.pdf",
            "sha256": "a" * 64,
            "mime_type": "application/pdf",
        }
        DocumentVersion.objects.create(**fields)
        with self.assertRaises(IntegrityError):
            DocumentVersion.objects.create(**fields)

    def test_unapproved_rule_cannot_create_production_run(self):
        rule = RuleVersion.objects.create(rule_code="RULE-1", version=1, status=RuleStatus.DRAFT)
        run = RecommendationRun(
            submission=self.submission,
            rule_version=rule,
            status="PENDING",
        )
        with self.assertRaises(ValidationError):
            run.full_clean()

    def test_approved_rule_can_create_run(self):
        rule = RuleVersion.objects.create(rule_code="RULE-1", version=1, status=RuleStatus.APPROVED)
        run = RecommendationRun.objects.create(submission=self.submission, rule_version=rule)
        self.assertEqual(run.rule_version_id, rule.id)
