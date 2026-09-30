# Phase 4 — Data Model

## Mục tiêu

Định nghĩa mô hình dữ liệu có provenance đầy đủ cho hồ sơ, chương trình đào tạo, rule, đề xuất AI, quyết định giáo viên, thông báo và audit.

## Nguyên tắc bắt buộc

- Dữ liệu nguồn và bằng chứng không bị ghi đè.
- Rule, curriculum và recommendation đều có version.
- Mọi kết quả xét phải truy ngược được về tài liệu, ô dữ liệu, rule version và model run.
- Không dùng AI recommendation làm quyết định cuối cùng.
- Migration phải mở rộng trước, backfill có kiểm soát, không xoá dữ liệu lịch sử.

## Trạng thái

Thiết kế dữ liệu đã hoàn tất ở mức đặc tả. Chưa tạo Django models/migrations triển khai; đó là bước code kế tiếp.

