# Phase 7 — Document Extraction

## Mục tiêu

Trích xuất text/metadata từ tài liệu, chuẩn hóa trường cơ bản và giữ evidence để người dùng kiểm tra.

## Nguyên tắc

- Kết quả extraction không phải quyết định miễn môn.
- Raw text, normalized value, confidence và evidence được lưu riêng.
- Trường không chắc chắn phải vào human-review queue.
- OCR/vision là adapter; không khóa hệ thống vào một provider.

