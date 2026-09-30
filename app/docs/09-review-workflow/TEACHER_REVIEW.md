# Teacher review

`POST /api/v1/recommendation-items/{id}/decision/`

- Teacher được phân công hoặc Admin mới được quyết định.
- Decision phải là `FULL`, `PARTIAL` hoặc `NOT_ELIGIBLE`.
- Nếu decision khác recommendation, bắt buộc có reason.
- Ghi `TeacherDecision` và `AuditEvent`.
- Khi mọi item đã có decision, submission chuyển `COMPLETED`; nếu chưa, giữ `TEACHER_REVIEW`.

