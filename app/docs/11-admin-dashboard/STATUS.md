# Phase 11 Status

- Dashboard tổng hợp hồ sơ, user role và AI usage theo provider/model/operation.
- Lọc theo ngày bắt đầu/kết thúc.
- Xuất CSV aggregate, không có dữ liệu định danh người học.
- API metrics và trang HTML đều giới hạn Admin.
- UserProfile role có trang quản lý trong Django Admin.
- Django system check đạt.

Cost chỉ phản ánh usage event và giá đã được ghi nhận. Tích hợp provider tự động, bảng giá cập nhật, biểu đồ và budget alert là phase AI/operations tiếp theo.

Production settings now fail closed on missing secret/hosts/PostgreSQL configuration, use secure cookies, HTTPS redirect and short HSTS. Domain-wide HSTS subdomains/preload remain opt-in pending domain-owner verification. Deployment still needs managed PostgreSQL/object storage, TLS/proxy, backups/restore, monitoring, dependency audit, and provisioned admin access; see `16-deployment/PRODUCTION.md`.
