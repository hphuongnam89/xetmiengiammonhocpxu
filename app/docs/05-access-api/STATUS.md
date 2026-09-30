# Phase 5 Status

## Đã hoàn thành

- API v1 cho `auth/me` và `submissions`.
- Session authentication, role permission, ownership filter.
- User/API throttle mặc định và trường teacher assignment.
- Login web bị giới hạn 10 lần/IP mỗi 15 phút; production dùng Redis TLS.
- Pagination, serializer validation và error envelope.
- Test suite hiện tại đạt 19/19.
- Django check và migration check đạt.

## Chưa đóng toàn bộ phase

- Chưa có token authentication cho mobile/external client.
- Chưa có giao diện/endpoint quản trị phân công teacher nâng cao.
- Upload, OCR, AI và notification thuộc phase sau.
