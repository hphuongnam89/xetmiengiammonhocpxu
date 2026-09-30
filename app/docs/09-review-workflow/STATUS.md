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

# Implementation update — 30/09/2026

- Sales/Admin can start a recommendation from `/app/submissions/{id}/review/` after the assigned teacher has assembled confirmed course rows.
- Teacher/Admin assembles each row explicitly in the document extraction screen; the UI never guesses which separate OCR fields belong together.
- The API receives row IDs plus rule/curriculum versions; it builds items only from persisted `HUMAN_ACCEPTED` fields and stores source/curriculum/mapping snapshots.
- One run per submission is explicitly marked current and displayed; only that run can receive decisions. UI/API smoke coverage uses synthetic academic data.
- Actual academic rules, mappings, and source curriculum still require the designated owner review. Rule definitions are gated but not yet interpreted by the evaluator; mappings still are not intrinsically version-bound to a curriculum.
