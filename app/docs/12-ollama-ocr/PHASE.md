# Phase 12 — Local OCR with Ollama

OCR adapter dùng Ollama vision tại `127.0.0.1:11434` mặc định. PDF scan được render tối đa 10 trang đầu bằng `pdftoppm`; ảnh JPG/PNG gửi trực tiếp. OCR output và evidence được giữ trong extraction run/fields; mọi field đều chờ người kiểm tra.
