# Handoff

## Acceptance

- [x] File hợp lệ được lưu và checksum được ghi nhận.
- [x] File quá lớn, sai MIME, extension hoặc signature bị từ chối.
- [x] Upload lặp lại tạo version mới, không ghi đè version cũ.
- [x] Người không có quyền không thể upload.

## Exclusions

- OCR/extraction.
- Virus scanning production.
- S3/private bucket deployment.
