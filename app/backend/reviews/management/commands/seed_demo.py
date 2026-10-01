import hashlib
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from reviews.models import (
    Course,
    CurriculumVersion,
    CurriculumVersionStatus,
    DocumentVersion,
    Program,
    Role,
    Student,
    Submission,
    SubmissionStatus,
    UserProfile,
)


class Command(BaseCommand):
    help = "Create reproducible synthetic Sales/Teacher data for local UAT only."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="demo-password-change-me")
        parser.add_argument("--with-documents", action="store_true")

    def handle(self, *args, **options):
        password = options["password"]
        User = get_user_model()

        admin, _ = User.objects.get_or_create(username="demo_admin", defaults={"is_staff": True})
        admin.is_staff = True
        admin.set_password(password)
        admin.save(update_fields=["is_staff", "password"])
        self._profile(admin, Role.ADMIN)

        sales, _ = User.objects.get_or_create(username="demo_sales")
        sales.set_password(password)
        sales.save(update_fields=["password"])
        self._profile(sales, Role.SALES)

        teacher, _ = User.objects.get_or_create(username="demo_teacher")
        teacher.set_password(password)
        teacher.save(update_fields=["password"])
        self._profile(teacher, Role.TEACHER)

        fixtures = {
            "DEMO-only-university-transcript.pdf": ("DEMO-BBA", "ACC1011", "Principles of Accounting", "Demo University Student A"),
            "DEMO-only-college-transcript.pdf": ("DEMO-DIG", "DIG.7.01", "Fundamentals of Graphic Design", "Demo College Student B"),
        }
        root = Path(settings.BASE_DIR).parent.parent / "test-fixtures" / "dossiers"
        created = 0
        for filename, (program_code, course_code, course_name, student_name) in fixtures.items():
            program, _ = Program.objects.get_or_create(code=program_code, defaults={"name": f"Demo {program_code}"})
            curriculum, _ = CurriculumVersion.objects.get_or_create(
                program=program,
                source_sha256=hashlib.sha256(program_code.encode()).hexdigest(),
                source_sheet="DEMO",
                defaults={
                    "version_label": "DEMO-v1",
                    "source_file": "synthetic demo fixture; not an academic source",
                },
            )
            course, _ = Course.objects.get_or_create(
                curriculum=curriculum,
                source_row=1,
                defaults={
                    "raw_code": course_code,
                    "raw_name": course_name,
                    "credits": 3,
                    "course_type": "DEMO_ONLY",
                    "source_cells": {"fixture": filename},
                    "review_status": "APPROVED",
                },
            )
            course.review_status = "APPROVED"
            course.save(update_fields=["review_status"])
            if curriculum.status != CurriculumVersionStatus.APPROVED:
                curriculum.status = CurriculumVersionStatus.APPROVED
                curriculum.approved_by = admin
                curriculum.approved_at = timezone.now()
                curriculum.save(update_fields=["status", "approved_by", "approved_at"])

            student, _ = Student.objects.get_or_create(
                student_code=f"{program_code}-STUDENT",
                defaults={"full_name": student_name, "program_code": program_code},
            )
            student.full_name = student_name
            student.program_code = program_code
            student.save(update_fields=["full_name", "program_code"])
            submission, _ = Submission.objects.get_or_create(
                student=student,
                owner=sales,
                defaults={"teacher": teacher, "status": SubmissionStatus.DRAFT},
            )
            submission.teacher = teacher
            submission.save(update_fields=["teacher", "updated_at"])

            if options["with_documents"]:
                source = root / filename
                content = source.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                if not DocumentVersion.objects.filter(submission=submission, sha256=sha256).exists():
                    storage_key = f"documents/{submission.id}/{sha256}.pdf"
                    default_storage.save(storage_key, source.open("rb"))
                    DocumentVersion.objects.create(
                        submission=submission,
                        document_type="TRANSCRIPT",
                        storage_key=storage_key,
                        sha256=sha256,
                        mime_type="application/pdf",
                    )
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Demo ready: demo_sales/demo_teacher/demo_admin; documents created={created}. "
            "Synthetic data only; do not use for academic decisions or production."
        ))

    @staticmethod
    def _profile(user, role):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != role:
            profile.role = role
            profile.save(update_fields=["role"])
