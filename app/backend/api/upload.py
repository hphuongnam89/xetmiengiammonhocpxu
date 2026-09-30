import hashlib
import uuid
from pathlib import Path

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import DocumentVersion, Role, Submission

from .permissions import user_role

MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
}


class DocumentUploadView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    def post(self, request, submission_id):
        submission = get_object_or_404(Submission, pk=submission_id)
        role = user_role(request.user)
        if role == Role.SALES and submission.owner_id != request.user.id:
            return Response({"error": {"code": "forbidden", "message": "Not allowed."}}, status=403)
        if role not in {Role.ADMIN, Role.SALES}:
            return Response({"error": {"code": "forbidden", "message": "Not allowed."}}, status=403)

        uploaded = request.FILES.get("file")
        document_type = str(request.data.get("document_type", "OTHER")).strip()[:50]
        if not uploaded:
            return Response({"error": {"code": "file_required", "message": "File is required."}}, status=400)
        if uploaded.size > MAX_BYTES:
            return Response({"error": {"code": "file_too_large", "message": "Maximum file size is 10 MB."}}, status=422)

        extension = Path(uploaded.name).suffix.lower()
        expected = ALLOWED.get(extension)
        if not expected or uploaded.content_type != expected[0]:
            return Response({"error": {"code": "invalid_file_type", "message": "Unsupported file type."}}, status=422)

        first_bytes = uploaded.read(len(expected[1]))
        uploaded.seek(0)
        if not first_bytes.startswith(expected[1]):
            return Response({"error": {"code": "invalid_file_signature", "message": "File content does not match its type."}}, status=422)

        digest = hashlib.sha256()
        for chunk in uploaded.chunks():
            digest.update(chunk)
        uploaded.seek(0)
        storage_key = f"documents/{submission.id}/{uuid.uuid4()}{extension}"
        default_storage.save(storage_key, uploaded)
        document = DocumentVersion.objects.create(
            submission=submission,
            document_type=document_type,
            storage_key=storage_key,
            sha256=digest.hexdigest(),
            mime_type=expected[0],
        )
        return Response(
            {"data": {"id": str(document.id), "document_type": document.document_type, "sha256": document.sha256}},
            status=status.HTTP_201_CREATED,
        )
