# Acceptance checklist

- [x] API prefix `/api/v1/`.
- [x] Session authentication mặc định cho API nội bộ.
- [x] `GET /auth/me` trả user và role.
- [x] Sales chỉ xem submission do mình sở hữu.
- [x] Teacher/Admin xem được queue theo quyền.
- [x] Chỉ Sales/Admin được tạo submission.
- [x] Serializer whitelist field và validate input.
- [x] Pagination hỗ trợ `per_page`, giới hạn tối đa 100.
- [x] Error response có envelope chuẩn, không trả stack trace.
- [x] Integrity/API tests đạt.
- [x] Throttle mặc định cho anonymous/user API.
- [ ] Token auth cho client ngoài browser.
- [x] Submission có teacher assignment và serializer kiểm tra role.
