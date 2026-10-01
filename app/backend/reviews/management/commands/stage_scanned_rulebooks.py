import hashlib
import json
import unicodedata
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from pypdf import PdfReader

from api.ollama_ocr import _pdf_page_images
from api.paddle_ocr import _recognize
from reviews.models import AuditEvent, RuleStatus, RuleVersion


class Command(BaseCommand):
    help = "Stage scanned policy PDFs as resumable, unverified local OCR drafts."

    def add_arguments(self, parser):
        parser.add_argument("--config", required=True)
        parser.add_argument("--apply", action="store_true", help="Run OCR and save drafts; otherwise validate sources only.")

    def handle(self, *args, **options):
        try:
            sources = json.loads(Path(options["config"]).read_text(encoding="utf-8"))
        except Exception as exc:
            raise CommandError("Could not read source manifest.") from exc
        if not isinstance(sources, list) or not sources:
            raise CommandError("Source manifest must be a non-empty list.")

        resolved = []
        for item in sources:
            configured_path = Path(item["path"]).expanduser()
            path = configured_path.resolve()
            if not path.is_file():
                # Windows filesystems may preserve NFC while manifests use NFD,
                # even though both strings render identically to a user.
                normalized_target = unicodedata.normalize("NFC", str(configured_path.resolve())).replace("\\", "/")
                path = next((candidate.resolve() for candidate in Path.cwd().rglob("*")
                             if unicodedata.normalize("NFC", str(candidate.resolve())).replace("\\", "/") == normalized_target), path)
            if not path.is_file() or not item.get("rule_code"):
                raise CommandError("Each configured PDF must exist and have a rule_code.")
            with path.open("rb") as stream:
                page_count = len(PdfReader(stream).pages)
            resolved.append((item, path, page_count, hashlib.sha256(path.read_bytes()).hexdigest()))
        self.stdout.write("Sources: " + ", ".join(f"{path.name} ({count} pages)" for _, path, count, _ in resolved))
        if not options["apply"]:
            self.stdout.write("No OCR or database changes. Re-run with --apply to stage drafts.")
            return

        for item, path, page_count, digest in resolved:
            latest = RuleVersion.objects.filter(rule_code=item["rule_code"]).order_by("-version").first()
            if latest and latest.source_reference.endswith(digest) and latest.status == RuleStatus.APPROVED:
                self.stdout.write(f"Already approved: {item['rule_code']} v{latest.version}; skipped.")
                continue
            if latest and latest.source_reference.endswith(digest) and latest.status == RuleStatus.DRAFT:
                rule = latest
                saved_pages = {page["page_number"]: page for page in rule.definition.get("pages", [])}
                self.stdout.write(f"Resuming {item['rule_code']} v{rule.version} at saved page evidence.")
            else:
                version = latest.version + 1 if latest else 1
                rule = RuleVersion.objects.create(
                    rule_code=item["rule_code"], version=version, status=RuleStatus.DRAFT,
                    source_reference=f"{path.name}#sha256:{digest}",
                    definition={
                        "kind": "scanned_source_ocr_draft", "verification_status": "UNVERIFIED_OCR",
                        "source_file": path.name, "source_sha256": digest,
                        "ocr_engine": "PaddleOCR/PP-OCRv6", "model": "",
                        "academic_owner_review": {"verified": False, "reviewer": "", "note": ""},
                        "pages": [],
                    },
                )
                saved_pages = {}
                AuditEvent.objects.create(actor=None, action="RULEBOOK_OCR_DRAFT_STAGED", entity_type="RuleVersion",
                    entity_id=str(rule.id), payload={"rule_code": rule.rule_code, "version": rule.version,
                                                     "source_sha256": digest, "page_count": page_count,
                                                     "verification_status": "UNVERIFIED_OCR"})

            with path.open("rb") as stream:
                images = _pdf_page_images(stream.read(), limit=page_count)
            if len(images) != page_count:
                raise CommandError(f"OCR page render count mismatch for {path.name}.")
            for page_number, image in enumerate(images, start=1):
                if page_number in saved_pages and saved_pages[page_number].get("raw_text"):
                    continue
                page_text, regions = _recognize(image)
                model = "PaddleOCR/PP-OCRv6"
                if not page_text:
                    raise CommandError(f"OCR returned blank text for {path.name}, page {page_number}; draft is resumable.")
                saved_pages[page_number] = {
                    "page_number": page_number, "raw_text": page_text,
                    "ocr_fields": regions,
                }
                definition = dict(rule.definition)
                definition["model"] = model
                definition["pages"] = [saved_pages[n] for n in sorted(saved_pages)]
                rule.definition = definition
                rule.save(update_fields=["definition"])
                AuditEvent.objects.create(actor=None, action="RULEBOOK_OCR_PAGE_STAGED", entity_type="RuleVersion",
                    entity_id=str(rule.id), payload={"rule_code": rule.rule_code, "version": rule.version,
                                                     "page_number": page_number, "page_count": page_count})
                self.stdout.write(f"{item['rule_code']}: OCR page {page_number}/{page_count}")
            self.stdout.write(f"Saved {len(saved_pages)}/{page_count} pages for {item['rule_code']} as DRAFT.")
        self.stdout.write("OCR drafts remain unverified and cannot drive decisions.")
