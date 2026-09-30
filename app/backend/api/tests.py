from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from reviews.models import (DocumentVersion, ExtractedField, ExtractionRun, FieldReviewStatus,
    RecommendationItem, Role, RuleStatus, RuleVersion, Student, Submission, UserProfile)
from api.extraction import _labeled_fields


class ApiAccessTests(APITestCase):
    def setUp(self):
        self.sales = User.objects.create_user(username="sales")
        UserProfile.objects.create(user=self.sales, role=Role.SALES)
        self.other_sales = User.objects.create_user(username="other-sales")
        UserProfile.objects.create(user=self.other_sales, role=Role.SALES)
        self.teacher = User.objects.create_user(username="teacher")
        UserProfile.objects.create(user=self.teacher, role=Role.TEACHER)
        self.student = Student.objects.create(student_code="SV-API", full_name="Test Student")
        Submission.objects.create(student=self.student, owner=self.other_sales)
        self.rule = RuleVersion.objects.create(rule_code="RULE-TEST", version=1, status=RuleStatus.APPROVED)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 403)

    def test_login_is_rate_limited_after_ten_attempts(self):
        cache.clear()
        for _ in range(10):
            response = self.client.post("/accounts/login/", {"username": "unknown", "password": "wrong"})
            self.assertEqual(response.status_code, 200)
        response = self.client.post("/accounts/login/", {"username": "unknown", "password": "wrong"})
        self.assertEqual(response.status_code, 429)

    def test_sales_only_sees_owned_submissions(self):
        self.client.force_authenticate(self.sales)
        response = self.client.get("/api/v1/submissions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_sales_can_create_owned_submission(self):
        self.client.force_authenticate(self.sales)
        response = self.client.post(
            "/api/v1/submissions/",
            {"student": str(self.student.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_sales_can_upload_valid_pdf(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales)
        self.client.force_authenticate(self.sales)
        response = self.client.post(
            f"/api/v1/submissions/{owned.id}/documents/",
            {"document_type": "TRANSCRIPT", "file": SimpleUploadedFile("marks.pdf", b"%PDF-1.7 data", content_type="application/pdf")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)

    def test_upload_rejects_signature_mismatch(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales)
        self.client.force_authenticate(self.sales)
        response = self.client.post(
            f"/api/v1/submissions/{owned.id}/documents/",
            {"file": SimpleUploadedFile("marks.pdf", b"not a pdf", content_type="application/pdf")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 422)

    def test_labeled_text_is_extracted_without_inventing_values(self):
        fields = _labeled_fields("Họ tên: Nguyen Van B\nTín chỉ: 3\nKhông có nhãn khác")
        self.assertEqual({field["field_key"] for field in fields}, {"student_name", "credits"})

    def test_image_extraction_requires_review(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales)
        self.client.force_authenticate(self.sales)
        upload = self.client.post(
            f"/api/v1/submissions/{owned.id}/documents/",
            {"file": SimpleUploadedFile("photo.png", b"\x89PNG\r\n\x1a\nimage", content_type="image/png")},
            format="multipart",
        )
        self.assertEqual(upload.status_code, 201)
        extraction = self.client.post(f"/api/v1/documents/{upload.data['data']['id']}/extract/")
        self.assertEqual(extraction.status_code, 200)
        self.assertEqual(extraction.data["data"]["status"], "NEEDS_REVIEW")

    def test_assigned_teacher_can_correct_ocr_without_changing_raw_evidence(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        document = DocumentVersion.objects.create(
            submission=owned, document_type="TRANSCRIPT", storage_key="private/test.png",
            sha256="a" * 64, mime_type="image/png",
        )
        run = ExtractionRun.objects.create(document=document, engine="ollama-vision", status="NEEDS_REVIEW")
        field = ExtractedField.objects.create(
            run=run, field_key="student_name", raw_value="OCR spelling", normalized_value="",
            evidence_text="source text", review_status=FieldReviewStatus.NEEDS_REVIEW,
        )
        self.client.force_login(self.teacher)
        response = self.client.post(f"/app/documents/{document.id}/extraction/", {
            "action": "review_field", "field_id": str(field.id),
            "normalized_value": "Verified spelling", "review_status": "AUTO_ACCEPTED",
        })
        self.assertEqual(response.status_code, 302)
        field.refresh_from_db()
        self.assertEqual(field.raw_value, "OCR spelling")
        self.assertEqual(field.normalized_value, "Verified spelling")
        self.assertEqual(field.review_status, FieldReviewStatus.AUTO_ACCEPTED)

    def test_unassigned_teacher_cannot_access_extraction_review(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales)
        document = DocumentVersion.objects.create(
            submission=owned, document_type="TRANSCRIPT", storage_key="private/test.png",
            sha256="b" * 64, mime_type="image/png",
        )
        self.client.force_login(self.teacher)
        response = self.client.get(f"/app/documents/{document.id}/extraction/")
        self.assertEqual(response.status_code, 403)

    def test_assigned_teacher_can_add_manually_verified_ocr_field(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        document = DocumentVersion.objects.create(
            submission=owned, document_type="TRANSCRIPT", storage_key="private/test.png",
            sha256="c" * 64, mime_type="image/png",
        )
        ExtractionRun.objects.create(document=document, engine="ollama-vision", status="NEEDS_REVIEW")
        self.client.force_login(self.teacher)
        response = self.client.post(f"/app/documents/{document.id}/extraction/", {
            "action": "add_field", "field_key": "credits", "normalized_value": "3",
            "evidence_text": "Số tín chỉ: 3", "page_number": "2",
        })
        self.assertEqual(response.status_code, 302)
        field = ExtractedField.objects.get(run__document=document)
        self.assertEqual(field.raw_value, "")
        self.assertEqual(field.normalized_value, "3")
        self.assertEqual(field.review_status, FieldReviewStatus.HUMAN_ACCEPTED)
        self.assertEqual(field.page_number, 2)

    def test_recommendation_run_is_idempotent_and_moves_to_teacher_review(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        self.client.force_authenticate(self.sales)
        payload = {
            "rule_version_id": str(self.rule.id),
            "idempotency_key": "run-1",
            "items": [{"course_code": "ACC101", "prior_grade": 8, "prior_credits": 3, "content_match": True, "evidence": ["p1"]}],
        }
        first = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", payload, format="json")
        second = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(RecommendationItem.objects.count(), 1)
        owned.refresh_from_db()
        self.assertEqual(owned.status, "TEACHER_REVIEW")

    def test_assigned_teacher_can_override_with_reason(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        self.client.force_authenticate(self.sales)
        run = self.client.post(
            f"/api/v1/submissions/{owned.id}/recommendations/",
            {"rule_version_id": str(self.rule.id), "idempotency_key": "run-2", "items": [{"course_code": "ACC101", "prior_grade": 8, "prior_credits": 3, "content_match": True, "evidence": ["p1"]}]},
            format="json",
        )
        item_id = run.data["data"]["items"][0]["id"]
        self.client.force_authenticate(self.teacher)
        response = self.client.post(f"/api/v1/recommendation-items/{item_id}/decision/", {"decision": "PARTIAL", "reason": "Need syllabus review."}, format="json")
        self.assertEqual(response.status_code, 200)
        owned.refresh_from_db()
        self.assertEqual(owned.status, "COMPLETED")
