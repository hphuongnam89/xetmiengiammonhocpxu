# Security

- File lưu trong `MEDIA_ROOT/documents/` và không public trực tiếp.
- Không tin MIME do client gửi; kiểm tra extension, MIME và kích thước.
- Tên file lưu do server sinh bằng UUID; không dùng tên file người dùng làm path.
- Không log nội dung tài liệu hoặc dữ liệu định danh nhạy cảm.
- Virus scanning, object storage private và OCR là hạng mục tiếp theo.

