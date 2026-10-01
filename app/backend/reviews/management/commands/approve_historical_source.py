from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from reviews.models import AuditEvent, HistoricalDecision, HistoricalDecisionStatus


class Command(BaseCommand):
    help = "Mark one user-confirmed, previously approved historical workbook as precedent data."

    def add_arguments(self, parser):
        parser.add_argument("--source-sha256", required=True)
        parser.add_argument("--review-note", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        source_hash = options["source_sha256"].strip().lower()
        note = options["review_note"].strip()
        if len(source_hash) != 64 or len(note) < 8:
            raise CommandError("Provide a SHA-256 hash and a specific source approval note.")
        rows = HistoricalDecision.objects.filter(source_sha256=source_hash)
        if not rows.exists():
            raise CommandError("No staged historical rows match that workbook checksum.")
        pending = rows.filter(status=HistoricalDecisionStatus.PENDING)
        if not pending.exists():
            self.stdout.write("No pending rows; source was already reviewed or has no usable decisions.")
            return
        now = timezone.now()
        count = pending.update(status=HistoricalDecisionStatus.APPROVED,
                               reviewed_at=now, review_note=note)
        AuditEvent.objects.create(actor=None, action="HISTORICAL_SOURCE_APPROVED_BY_USER_CONFIRMATION",
            entity_type="HistoricalWorkbook", entity_id=source_hash[:32],
            payload={"source_sha256": source_hash, "approved_rows": count,
                     "review_note": note, "reviewed_by_user_account": False})
        self.stdout.write(f"Approved {count} staged rows from source {source_hash}.")
