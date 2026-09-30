from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from reviews.models import AuditEvent, Course, CurriculumVersion, CurriculumVersionStatus


PROGRAM_CODES = ("INTERNAL-QTKD", "INTERNAL-NNT", "INTERNAL-NNA", "INTERNAL-DHKTS", "INTERNAL-DL")


class Command(BaseCommand):
    help = "Approve the five explicitly authorized imported curriculum sheets."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Apply the activation; otherwise show a preview.")

    def handle(self, *args, **options):
        curricula = list(CurriculumVersion.objects.filter(program_id__in=PROGRAM_CODES).order_by("program_id"))
        if len(curricula) != len(PROGRAM_CODES) or {c.program_id for c in curricula} != set(PROGRAM_CODES):
            raise CommandError("Expected exactly one imported curriculum for each of the five configured programs.")
        courses = Course.objects.filter(curriculum__in=curricula)
        total = courses.count()
        eligible = courses.exclude(raw_code="").exclude(raw_name="").count()
        structural = total - eligible
        if total != 380 or eligible != 301 or structural != 79:
            raise CommandError(f"Unexpected source row counts: total={total}, eligible={eligible}, structural={structural}.")
        already_done = all(c.status == CurriculumVersionStatus.APPROVED for c in curricula)
        if already_done:
            self.stdout.write("Already activated; no changes made.")
            return
        if any(c.status != CurriculumVersionStatus.DRAFT for c in curricula):
            raise CommandError("Mixed curriculum statuses; inspect before activation.")
        self.stdout.write(f"Preview: approve {len(curricula)} curricula; approve {eligible} course rows; retain {structural} structural rows.")
        if not options["apply"]:
            self.stdout.write("No changes made. Re-run with --apply to activate.")
            return
        now = timezone.now()
        with transaction.atomic():
            CurriculumVersion.objects.filter(pk__in=[c.pk for c in curricula]).update(
                status=CurriculumVersionStatus.APPROVED, approved_at=now,
            )
            courses.filter(raw_code__gt="", raw_name__gt="").update(review_status="APPROVED")
            courses.filter(raw_code="").update(review_status="STRUCTURE")
            courses.filter(raw_name="").update(review_status="STRUCTURE")
            AuditEvent.objects.create(
                actor=None,
                action="CURRICULA_ACTIVATED_BY_USER_AUTHORIZATION",
                entity_type="CurriculumBatch",
                entity_id="imported-380",
                payload={
                    "authorization": "User instructed to use the 380 imported curriculum rows now; future changes will be handled later.",
                    "curriculum_ids": [str(c.pk) for c in curricula],
                    "curriculum_programs": list(PROGRAM_CODES),
                    "source_rows": total,
                    "approved_course_rows": eligible,
                    "structural_rows_retained": structural,
                    "approved_by_user_account": False,
                },
            )
        self.stdout.write("Activated: 5 curricula, 301 course rows; 79 structural rows retained.")
