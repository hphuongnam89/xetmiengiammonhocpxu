# UI workflow

- `/app/`: dashboard theo role, danh sách hồ sơ và notification.
- `/app/submissions/{id}/review/`: teacher/admin xem recommendation, evidence, quyết định từng môn và ghi lý do khi override.
- `/accounts/login/`: đăng nhập session; form POST có CSRF.
- Sales thấy hồ sơ mình phụ trách; teacher thấy hồ sơ được giao; admin thấy danh sách hệ thống.

