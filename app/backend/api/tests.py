from pathlib import Path

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from reviews.models import (DocumentVersion, ExtractedField, ExtractionRun, FieldReviewStatus,
    Course, CurriculumVersion, CurriculumVersionStatus, ExtractedCourseRow, MappingStatus, Program,
    RecommendationItem, Role, RuleMappingVersion, RuleStatus, RuleVersion, Student, Submission, UserProfile)
from api.extraction import _labeled_fields
from api.recommendation_service import create_course_row


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
        self.rule = RuleVersion.objects.create(rule_code="RULE-TEST", version=1, status=RuleStatus.APPROVED,
            definition={"rules": [{"rule_id": "test-only"}], "academic_owner_review":
                {"verified": True, "reviewer": "Test fixture", "note": "Synthetic test data only."}})

    def make_upload_program(self):
        program = Program.objects.create(code="UPLOAD-TEST", name="Upload test program")
        curriculum = CurriculumVersion.objects.create(program=program, version_label="Synthetic v1",
            source_file="synthetic.xlsx", source_sha256="f" * 64, source_sheet="Test",
            status=CurriculumVersionStatus.APPROVED)
        return program, curriculum

    def demo_diploma(self, name="DEMO-only-university-transcript.pdf"):
        path = Path(__file__).resolve().parents[3] / "test-fixtures" / "dossiers" / name
        return path.read_bytes()

    def test_submission_form_has_separate_degree_and_transcript_inputs_without_student_number(self):
        self.make_upload_program()
        self.client.force_login(self.sales)
        response = self.client.get("/app/submissions/new/")
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="diploma_file"', html)
        self.assertIn('name="transcript_file_1"', html)
        self.assertIn('name="transcript_file_2"', html)
        self.assertNotIn('name="student_code"', html)
        self.assertIn('name="full_name"', html)

    def test_degree_preview_extracts_name_from_text_pdf(self):
        self.client.force_login(self.sales)
        response = self.client.post("/app/submissions/preview-degree-name/", {
            "diploma_file": SimpleUploadedFile("diploma.pdf", self.demo_diploma(), content_type="application/pdf"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["full_name"], "Demo University Student A")

    def test_sales_creates_case_with_separate_document_types_and_generated_internal_code(self):
        program, _curriculum = self.make_upload_program()
        self.client.force_login(self.sales)
        second_transcript = self.demo_diploma() + b"\n% distinct second transcript fixture\n"
        response = self.client.post("/app/submissions/new/", {
            "full_name": "Demo University Student A", "program_code": program.code,
            "teacher_id": str(self.teacher.id),
            "diploma_file": SimpleUploadedFile("diploma.pdf", self.demo_diploma(), content_type="application/pdf"),
            "transcript_file_1": SimpleUploadedFile("transcript-1.pdf", self.demo_diploma("DEMO-only-college-transcript.pdf"), content_type="application/pdf"),
            "transcript_file_2": SimpleUploadedFile("transcript-2.pdf", second_transcript, content_type="application/pdf"),
        })
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(owner=self.sales, student__full_name="Demo University Student A")
        self.assertTrue(submission.student.student_code.startswith("INCOMING-"))
        self.assertEqual(set(submission.documents.values_list("document_type", flat=True)),
                         {"DIPLOMA", "TRANSCRIPT_1", "TRANSCRIPT_2"})

    def make_course_row(self, submission, *, mapped=True, grade_value="8.0"):
        program = Program.objects.create(code="TEST", name="Test program")
        curriculum = CurriculumVersion.objects.create(program=program, version_label="Synthetic v1", source_file="synthetic.xlsx",
            source_sha256="d" * 64, source_sheet="Test")
        target = Course.objects.create(curriculum=curriculum, raw_code="ACC101", raw_name="Accounting", source_row=1, review_status="APPROVED")
        curriculum.status = CurriculumVersionStatus.APPROVED
        curriculum.save(update_fields=["status"])
        if mapped:
            RuleMappingVersion.objects.create(mapping_code="TEST-MAP", version=1, source_course="Basic Accounting",
                target_course_code="ACC101", mapping_data={"academic_owner_review":
                    {"verified": True, "reviewer": "Test fixture", "note": "Synthetic test data only."}},
                source_reference="Synthetic test source", status=MappingStatus.APPROVED, created_by=self.sales)
        document = DocumentVersion.objects.create(submission=submission, document_type="TRANSCRIPT", storage_key="private/test.pdf",
            sha256="e" * 64, mime_type="application/pdf")
        extraction = ExtractionRun.objects.create(document=document, engine="test", status="COMPLETED")
        name = ExtractedField.objects.create(run=extraction, field_key="course_name", raw_value="Basic Accounting",
            normalized_value="Basic Accounting", evidence_text="Basic Accounting", page_number=1,
            review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        grade = ExtractedField.objects.create(run=extraction, field_key="grade", raw_value=grade_value, normalized_value=grade_value,
            evidence_text=f"Grade: {grade_value}", page_number=1, review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        credits = ExtractedField.objects.create(run=extraction, field_key="credits", raw_value="3", normalized_value="3",
            evidence_text="Credits: 3", page_number=1, review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        row = create_course_row(submission=submission, actor=self.teacher, name_field=name, grade_field=grade,
            credits_field=credits, code_field=None, target_course=target)
        return curriculum, row, name, grade, credits

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
        curriculum, row, name, grade, credits = self.make_course_row(owned)
        self.client.force_authenticate(self.sales)
        payload = {
            "rule_version_id": str(self.rule.id),
            "curriculum_version_id": str(curriculum.id),
            "idempotency_key": "run-1",
            "course_row_ids": [str(row.id)],
        }
        first = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", payload, format="json")
        second = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(RecommendationItem.objects.count(), 1)
        result = RecommendationItem.objects.get()
        self.assertEqual(result.recommendation, "FULL")
        self.assertEqual(result.evidence[0]["field_id"], str(name.id))
        self.assertEqual(result.evidence[0]["document_sha256"], "e" * 64)
        self.assertEqual(result.run.curriculum_version_id, curriculum.id)
        owned.refresh_from_db()
        self.assertEqual(owned.status, "TEACHER_REVIEW")

    def test_recommendation_does_not_accept_caller_supplied_items(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales)
        self.client.force_authenticate(self.sales)
        response = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", {
            "rule_version_id": str(self.rule.id), "idempotency_key": "forged",
            "items": [{"course_code": "ACC101", "prior_grade": 10, "prior_credits": 100,
                       "content_match": True, "evidence": ["made up"]}],
        }, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(RecommendationItem.objects.count(), 0)

    def test_reusing_idempotency_key_with_different_curriculum_is_rejected(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        curriculum, row, *_ = self.make_course_row(owned)
        self.client.force_authenticate(self.sales)
        path = f"/api/v1/submissions/{owned.id}/recommendations/"
        payload = {"rule_version_id": str(self.rule.id), "curriculum_version_id": str(curriculum.id),
                   "idempotency_key": "stable-key", "course_row_ids": [str(row.id)]}
        self.assertEqual(self.client.post(path, payload, format="json").status_code, 201)
        other_program = Program.objects.create(code="OTHER", name="Other")
        other_curriculum = CurriculumVersion.objects.create(program=other_program, version_label="Other v1",
            source_file="synthetic.xlsx", source_sha256="b" * 64, source_sheet="Test")
        other_curriculum.status = CurriculumVersionStatus.APPROVED
        other_curriculum.save(update_fields=["status"])
        payload["curriculum_version_id"] = str(other_curriculum.id)
        response = self.client.post(path, payload, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["error"]["code"], "idempotency_key_conflict")

    def test_unassigned_teacher_cannot_decide_a_recommendation(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        curriculum, row, *_ = self.make_course_row(owned)
        self.client.force_authenticate(self.sales)
        run = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", {
            "rule_version_id": str(self.rule.id), "curriculum_version_id": str(curriculum.id),
            "idempotency_key": "teacher-boundary", "course_row_ids": [str(row.id)],
        }, format="json")
        item_id = run.data["data"]["items"][0]["id"]
        self.client.force_authenticate(self.other_sales)
        response = self.client.post(f"/api/v1/recommendation-items/{item_id}/decision/", {
            "decision": "FULL", "reason": "Not assigned.",
        }, format="json")
        self.assertEqual(response.status_code, 403)

    def test_superseded_run_cannot_receive_teacher_decision(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        curriculum, row, *_ = self.make_course_row(owned)
        self.client.force_authenticate(self.sales)
        path = f"/api/v1/submissions/{owned.id}/recommendations/"
        body = {"rule_version_id": str(self.rule.id), "curriculum_version_id": str(curriculum.id),
                "idempotency_key": "first-run", "course_row_ids": [str(row.id)]}
        first = self.client.post(path, body, format="json")
        old_item_id = first.data["data"]["items"][0]["id"]
        body["idempotency_key"] = "second-run"
        self.assertEqual(self.client.post(path, body, format="json").status_code, 201)
        self.client.force_authenticate(self.teacher)
        response = self.client.post(f"/api/v1/recommendation-items/{old_item_id}/decision/", {
            "decision": "FULL", "reason": "Old result.",
        }, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_approved_mapping_stays_in_human_review(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        curriculum, row, *_ = self.make_course_row(owned, mapped=False, grade_value="2")
        self.client.force_authenticate(self.sales)
        response = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", {
            "rule_version_id": str(self.rule.id), "curriculum_version_id": str(curriculum.id),
            "idempotency_key": "no-map", "course_row_ids": [str(row.id)],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        item = RecommendationItem.objects.get()
        self.assertEqual(item.recommendation, "NEEDS_HUMAN_REVIEW")
        self.assertIn("Chưa có mapping", item.rationale)

    def test_sales_and_teacher_can_complete_the_ui_recommendation_flow(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        curriculum, row, *_ = self.make_course_row(owned)
        self.client.force_login(self.sales)
        response = self.client.post(f"/app/submissions/{owned.id}/review/", {
            "action": "create_recommendation", "rule_version_id": str(self.rule.id),
            "curriculum_version_id": str(curriculum.id), "idempotency_key": "ui-run-1",
            "course_row_ids": [str(row.id)],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RecommendationItem.objects.count(), 1)
        response = self.client.get(f"/app/submissions/{owned.id}/review/")
        self.assertContains(response, "Lượt đề xuất hiện hành")
        self.assertContains(response, "TEST-MAP")
        self.client.force_login(self.teacher)
        response = self.client.get(f"/app/submissions/{owned.id}/review/")
        self.assertContains(response, "Quyết định giảng viên")
        item = RecommendationItem.objects.get()
        response = self.client.post(f"/app/submissions/{owned.id}/review/", {
            "action": "teacher_decision", "item_id": str(item.id), "decision": "FULL",
        })
        self.assertEqual(response.status_code, 302)
        owned.refresh_from_db()
        self.assertEqual(owned.status, "COMPLETED")

    def test_course_row_rejects_unconfirmed_fields(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        program = Program.objects.create(code="TEST", name="Test program")
        curriculum = CurriculumVersion.objects.create(program=program, version_label="v1", source_file="synthetic.xlsx",
            source_sha256="f" * 64, source_sheet="Test")
        target = Course.objects.create(curriculum=curriculum, raw_code="ACC101", raw_name="Accounting", source_row=1, review_status="APPROVED")
        curriculum.status = CurriculumVersionStatus.APPROVED
        curriculum.save(update_fields=["status"])
        document = DocumentVersion.objects.create(submission=owned, document_type="TRANSCRIPT", storage_key="private/test.pdf",
            sha256="a" * 64, mime_type="application/pdf")
        extraction = ExtractionRun.objects.create(document=document, engine="test", status="COMPLETED")
        name = ExtractedField.objects.create(run=extraction, field_key="course_name", raw_value="Basic Accounting",
            normalized_value="Basic Accounting", evidence_text="Basic Accounting", review_status=FieldReviewStatus.NEEDS_REVIEW)
        grade = ExtractedField.objects.create(run=extraction, field_key="grade", raw_value="8", normalized_value="8",
            evidence_text="Grade: 8", review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        credits = ExtractedField.objects.create(run=extraction, field_key="credits", raw_value="3", normalized_value="3",
            evidence_text="Credits: 3", review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        with self.assertRaises(ValueError):
            create_course_row(submission=owned, actor=self.teacher, name_field=name, grade_field=grade,
                credits_field=credits, code_field=None, target_course=target)
        self.assertEqual(ExtractedCourseRow.objects.count(), 0)

    def test_course_row_requires_source_evidence(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        program = Program.objects.create(code="TEST", name="Test program")
        curriculum = CurriculumVersion.objects.create(program=program, version_label="v1", source_file="synthetic.xlsx",
            source_sha256="c" * 64, source_sheet="Test")
        target = Course.objects.create(curriculum=curriculum, raw_code="ACC101", raw_name="Accounting", source_row=1, review_status="APPROVED")
        curriculum.status = CurriculumVersionStatus.APPROVED
        curriculum.save(update_fields=["status"])
        document = DocumentVersion.objects.create(submission=owned, document_type="TRANSCRIPT", storage_key="private/test.pdf",
            sha256="9" * 64, mime_type="application/pdf")
        extraction = ExtractionRun.objects.create(document=document, engine="test", status="COMPLETED")
        name = ExtractedField.objects.create(run=extraction, field_key="course_name", normalized_value="Basic Accounting",
            review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        grade = ExtractedField.objects.create(run=extraction, field_key="grade", normalized_value="8", evidence_text="Grade 8",
            review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        credits = ExtractedField.objects.create(run=extraction, field_key="credits", normalized_value="3", evidence_text="Credits 3",
            review_status=FieldReviewStatus.HUMAN_ACCEPTED)
        with self.assertRaises(ValueError):
            create_course_row(submission=owned, actor=self.teacher, name_field=name, grade_field=grade,
                credits_field=credits, code_field=None, target_course=target)

    def test_assigned_teacher_can_override_with_reason(self):
        owned = Submission.objects.create(student=self.student, owner=self.sales, teacher=self.teacher)
        self.client.force_authenticate(self.sales)
        run = self.client.post(
            f"/api/v1/submissions/{owned.id}/recommendations/",
            {"rule_version_id": str(self.rule.id), "curriculum_version_id": "bad", "idempotency_key": "run-2", "course_row_ids": []},
            format="json",
        )
        self.assertEqual(run.status_code, 422)
        curriculum, row, *_ = self.make_course_row(owned)
        run = self.client.post(f"/api/v1/submissions/{owned.id}/recommendations/", {
            "rule_version_id": str(self.rule.id), "curriculum_version_id": str(curriculum.id),
            "idempotency_key": "run-2", "course_row_ids": [str(row.id)],
        }, format="json")
        item_id = run.data["data"]["items"][0]["id"]
        self.client.force_authenticate(self.teacher)
        response = self.client.post(f"/api/v1/recommendation-items/{item_id}/decision/", {"decision": "PARTIAL", "reason": "Need syllabus review."}, format="json")
        self.assertEqual(response.status_code, 200)
        owned.refresh_from_db()
        self.assertEqual(owned.status, "COMPLETED")
