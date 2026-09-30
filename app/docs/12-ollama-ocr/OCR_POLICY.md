# OCR policy

- Provider mặc định chạy local qua Ollama; endpoint/model có thể cấu hình bằng `OLLAMA_BASE_URL`, `OLLAMA_VISION_MODEL`.
- Không gửi ra provider bên ngoài theo mặc định.
- OCR không phê duyệt miễn môn và không tự xác nhận field.
- Lưu model, raw text, evidence, confidence và token usage; local cost ghi 0.
- PDF scan giới hạn 10 trang đầu trong adapter hiện tại; trang còn lại cần xử lý riêng.
