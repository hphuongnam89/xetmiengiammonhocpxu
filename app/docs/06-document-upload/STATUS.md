# Phase 6 Status

## Đã hoàn thành

- Endpoint upload multipart cho submission.
- Allowlist PDF/JPEG/PNG, kiểm tra MIME + extension + file signature.
- Giới hạn kích thước 10 MB.
- SHA-256 và storage key UUID.
- DocumentVersion immutable theo checksum constraint.
- 2 upload security tests; tổng API/data tests đạt 8/8.

## Chưa thuộc phase hoàn thành

- OCR/extraction.
- Antivirus scanning production.
- Private S3/object storage deployment và signed download URL.
