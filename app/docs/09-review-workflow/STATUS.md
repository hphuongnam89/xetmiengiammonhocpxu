# Phase 9 Status

## Đã triển khai

- Recommendation run từ rule version `APPROVED`.
- Idempotency key chống tạo trùng run.
- Recommendation item lưu snapshot evidence/reason/confidence.
- Teacher/Admin quyết định từng item.
- Override bắt buộc reason.
- AuditEvent ghi hành động teacher decision.
- Submission tự chuyển `TEACHER_REVIEW` rồi `COMPLETED` khi đủ quyết định.
- Migration `0004_recommendationrun_idempotency_key_and_more`.
- Tổng test đạt 15/15.

## Chưa thuộc phase đóng

- Notification cho Sales/Teacher.
- UI review và chỉnh sửa trực quan.
- Rule cap toàn hồ sơ và detailed mappings cần academic approval.
