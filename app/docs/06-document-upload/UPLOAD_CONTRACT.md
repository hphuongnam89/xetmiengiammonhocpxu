# Upload contract

Endpoint: `POST /api/v1/submissions/{id}/documents/`

- Authentication bắt buộc.
- Sales chỉ upload vào submission mình sở hữu; Admin có thể upload; Teacher chỉ đọc.
- Multipart field: `file`, `document_type`.
- Tối đa 10 MB.
- MIME allowlist: `application/pdf`, `image/jpeg`, `image/png`.
- Extension allowlist: `.pdf`, `.jpg`, `.jpeg`, `.png`.
- Lưu checksum SHA-256 và tạo `DocumentVersion` mới; không ghi đè file cũ.

