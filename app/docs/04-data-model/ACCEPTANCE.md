# Acceptance checklist

- [ ] Mỗi bảng nghiệp vụ có primary key, timestamps và owner phù hợp.
- [ ] Foreign key không cho phép recommendation trỏ tới rule/curriculum không tồn tại.
- [ ] Chỉ `RuleVersion=APPROVED` mới được dùng cho run production.
- [ ] `DocumentVersion`, `SourceEvidence`, `RecommendationItem`, `AuditEvent` không bị ghi đè.
- [ ] Teacher decision lưu được người sửa, lý do và thời điểm.
- [ ] Có unique/idempotency key cho upload, import và recommendation run.
- [ ] Có index cho submission status, teacher queue, checksum và correlation id.
- [ ] Có kế hoạch backup, restore test và rollback được review trước production.
- [ ] Có kiểm thử tenant/role boundary để sales không xem hồ sơ ngoài phạm vi.

