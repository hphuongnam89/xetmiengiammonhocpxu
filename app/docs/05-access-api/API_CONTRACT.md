# API contract

Base path: `/api/v1/`

| Method | Endpoint | Quyền | Mục đích |
|---|---|---|---|
| GET | `/auth/me` | authenticated | Thông tin user và role |
| GET | `/submissions` | authenticated | Sales xem hồ sơ của mình; teacher/admin xem queue theo quyền |
| POST | `/submissions` | sales/admin | Tạo hồ sơ |
| GET | `/submissions/{id}` | authenticated | Xem hồ sơ theo ownership/role |
| PATCH | `/submissions/{id}` | admin/owner sales/teacher review | Cập nhật trường được phép |

Response lỗi dùng `{error: {code, message, details}}`, không trả stack trace.
Danh sách có pagination page/per_page. Input phải được validate bởi serializer.

