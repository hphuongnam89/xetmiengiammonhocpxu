# Phase 8 — Deterministic Rule Engine

## Mục tiêu

Tạo recommendation có thể tái lập từ rule version đã được duyệt, curriculum evidence và dữ liệu hồ sơ.

## Nguyên tắc

- LLM không được tự quyết định.
- Mỗi môn có recommendation, reason, confidence và evidence.
- Thiếu mapping hoặc thiếu evidence luôn chuyển `NEEDS_HUMAN_REVIEW`.
- Recommendation không phải teacher decision.

