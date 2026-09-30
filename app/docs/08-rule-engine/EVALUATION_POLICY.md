# Evaluation policy

- Rule phải có trạng thái `APPROVED`.
- Điểm thiếu, tín chỉ thiếu, certificate hết hạn, mapping chưa được duyệt hoặc evidence rỗng không được tự động miễn.
- Điểm từ 5/10 trở lên chỉ là điều kiện cần; vẫn phải so sánh nội dung/khối lượng/đánh giá.
- Cap 50% phải tính ở cấp toàn hồ sơ, không tính độc lập từng môn.
- LLM chỉ được dùng để hỗ trợ extraction/rationale có kiểm soát, không được thay deterministic evaluator.
- Content/course match phải xuất phát từ RuleMappingVersion đã duyệt ở server; không nhận cờ khớp do client tự khai.
