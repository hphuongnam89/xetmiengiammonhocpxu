# Handoff

## Đã có

- Đặc tả entity và quan hệ.
- Nguyên tắc provenance, versioning, immutability.
- Runbook migration an toàn.
- Acceptance checklist cho bước triển khai.

## Chưa có

- Django models và migrations thực tế.
- API contract và serializer.
- Seed roles/rules.
- Backup/restore automation.

## Bước kế tiếp

Implement models tối thiểu cho `User`, `Role`, `Student`, `Submission`, `DocumentVersion`, `RuleVersion`, `RecommendationRun`, `RecommendationItem`, `TeacherDecision`, `AuditEvent`, `AIUsageEvent`; sau đó chạy migration và test integrity.

