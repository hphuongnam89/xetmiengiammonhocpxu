# Phase 15 Status

- Có HistoricalDecision staging model, raw source-cell evidence và trạng thái review.
- Có importer theo explicit column config, dry-run, decision normalization và idempotency.
- Student reference tùy chọn chỉ lưu dạng SHA-256; không lưu tên sinh viên từ lịch sử.
- Admin approve/reject, ghi actor/time/audit; approved record immutable.
- Recommendation chỉ tham chiếu tổng hợp precedent approved đúng chương trình/môn như context.
- Chưa import tất cả sheet lịch sử do chưa có config/header/decision map được xác nhận cho từng sheet.
- Đã xác nhận workbook lịch sử có nhiều biến thể header; importer hỗ trợ cột outcome riêng và giữ mọi row ở PENDING.
- Đã staging workbook `16 SV KHUNG CŨ...` theo mapping có cột công nhận toàn phần/một phần: 16 sheet khớp cấu trúc, 107 sheet không khớp được bỏ qua, 155 dòng có kết quả trên 13 sheet (132 FULL, 23 PARTIAL). Tất cả vẫn PENDING.
- Tên sheet chứa họ tên không được lưu; chỉ lưu số thứ tự sheet, checksum, vị trí ô và dòng nguồn. Không có precedent nào tự động được duyệt.
- 107 sheet bỏ qua và các workbook lịch sử khác vẫn cần phân loại/cấu hình; 155 dòng cần người có thẩm quyền kiểm tra trước khi dùng làm precedent.
