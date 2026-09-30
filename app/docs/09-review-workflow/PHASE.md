# Phase 9 — Recommendation and Teacher Review

## Mục tiêu

Kết nối deterministic rule engine với recommendation snapshot và cho teacher/admin quyết định cuối từng môn.

## Nguyên tắc

- Chỉ rule version `APPROVED` mới tạo run.
- Run/item là snapshot; không ghi đè kết quả engine.
- Teacher decision là dữ liệu riêng, có người duyệt, thời điểm và lý do.
- Không tự động biến recommendation thành quyết định cuối.

