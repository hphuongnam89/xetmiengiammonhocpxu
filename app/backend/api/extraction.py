import re
from decimal import Decimal, InvalidOperation

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import (
    ExtractedField,
    ExtractionRun,
    ExtractionStatus,
    FieldReviewStatus,
    Role,
    DocumentVersion,
    AIUsageEvent,
)

from .permissions import user_role
from .ollama_ocr import extract_images


def _labeled_fields(text):
    patterns = {
        "student_name": r"(?:họ\s*tên|student\s*name)\s*[:\-]\s*(.+)",
        "school_name": r"(?:trường|school)\s*[:\-]\s*(.+)",
        "program": r"(?:ngành|program|major)\s*[:\-]\s*(.+)",
        "credits": r"(?:tín\s*chỉ|credits?)\s*[:\-]\s*([0-9]+(?:[.,][0-9]+)?)",
        "grade": r"(?:điểm|grade)\s*[:\-]\s*([0-9]+(?:[.,][0-9]+)?|[A-F][+]?)",
    }
    fields = []
    for key, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()[:1000]
            fields.append({"field_key": key, "raw_value": value, "confidence": 0.75})
    return fields


def extract_document(document):
    run = ExtractionRun.objects.create(document=document, engine="pypdf-text", status=ExtractionStatus.PENDING)
    with default_storage.open(document.storage_key, "rb") as source:
        content = source.read()
    pdf_text = ""
    if document.mime_type == "application/pdf":
        from pypdf import PdfReader
        import io
        pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
    if pdf_text.strip():
        run.raw_text = pdf_text
        run.status = ExtractionStatus.COMPLETED
        run.save(update_fields=["raw_text", "status"])
        for field in _labeled_fields(pdf_text):
            ExtractedField.objects.create(run=run, field_key=field["field_key"], raw_value=field["raw_value"],
                normalized_value=field["raw_value"], confidence=field["confidence"],
                review_status=FieldReviewStatus.NEEDS_REVIEW, evidence_text=field["raw_value"])
        return run
    try:
        pages, usage = extract_images(document, content)
        run.engine = "ollama-vision"
        run.model_version = usage[0]["model"] if usage else ""
        run.raw_text = "\n".join(page["raw_text"] for page in pages)
        run.status = ExtractionStatus.NEEDS_REVIEW
        run.save(update_fields=["engine", "model_version", "raw_text", "status"])
        allowed_fields = {"student_name", "school_name", "program", "course_name", "course_code", "credits", "grade", "document_date"}
        for page in pages:
            for field in page["fields"] if isinstance(page["fields"], list) else []:
                key = str(field.get("field_key", ""))[:100]
                value = str(field.get("raw_value", ""))[:1000]
                if key not in allowed_fields or not value:
                    continue
                try:
                    confidence = max(Decimal("0"), min(Decimal("1"), Decimal(str(field.get("confidence", 0)))))
                except (InvalidOperation, ValueError):
                    confidence = Decimal("0")
                ExtractedField.objects.create(run=run, field_key=key, raw_value=value, normalized_value="",
                    confidence=confidence, page_number=page["page_number"],
                    evidence_text=str(field.get("evidence_text", value))[:2000],
                    review_status=FieldReviewStatus.NEEDS_REVIEW)
        for event in usage:
            AIUsageEvent.objects.create(provider="ollama", model_name=event["model"], operation="document_ocr",
                input_tokens=event["input_tokens"], output_tokens=event["output_tokens"], cost=0)
    except Exception:
        run.engine = "ollama-vision"
        run.status = ExtractionStatus.NEEDS_REVIEW
        run.save(update_fields=["engine", "status"])
    return run


class DocumentExtractionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, document_id):
        document = get_object_or_404(DocumentVersion.objects.select_related("submission"), pk=document_id)
        role = user_role(request.user)
        if role == Role.SALES and document.submission.owner_id != request.user.id:
            return Response({"error": {"code": "forbidden", "message": "Not allowed."}}, status=403)
        if role not in {Role.ADMIN, Role.SALES}:
            return Response({"error": {"code": "forbidden", "message": "Not allowed."}}, status=403)
        run = extract_document(document)
        return Response({"data": {"id": str(run.id), "status": run.status, "raw_text": run.raw_text}})
