# Security checklist

- [ ] Production dùng HTTPS, secure cookie và secret từ environment.
- [ ] SessionAuthentication giữ CSRF cho request thay đổi dữ liệu.
- [ ] Tất cả endpoint protected mặc định; public endpoint phải ghi rõ.
- [ ] Serializer whitelist field và giới hạn độ dài input.
- [ ] Object-level permission kiểm tra role và ownership.
- [ ] Error response không lộ stack trace, SQL, file path hoặc secret.
- [ ] Có throttle cho endpoint login/upload/AI ở phase tương ứng.
- [ ] CORS production chỉ allowlist domain được duyệt.

