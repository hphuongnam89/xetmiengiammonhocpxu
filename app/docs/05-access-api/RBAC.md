# RBAC

- `ADMIN`: toàn quyền quản trị trong phạm vi hệ thống.
- `SALES`: tạo và xem/sửa submission do mình phụ trách; không xem hồ sơ sales khác.
- `TEACHER`: xem queue được phân công hoặc queue giảng viên; cập nhật trạng thái review, không sửa ownership.

Kiểm tra role phải nằm ở permission/service layer, không chỉ ẩn nút trên UI.

