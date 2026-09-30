# Phase 12 Status

- Ollama vision adapter cho ảnh và PDF scan.
- PDF có text layer tiếp tục dùng pypdf.
- Lưu field/evidence/page/confidence; mọi field `NEEDS_REVIEW`.
- Ghi input/output token theo model vào AIUsageEvent; local cost bằng 0.
- Chưa tích hợp provider cloud, queue bất đồng bộ hoặc xử lý mọi trang tài liệu dài.
