# Phase 14 Status

- Có Program, CurriculumVersion và Course model.
- Có management command import một sheet theo cấu hình tường minh, hỗ trợ dry-run và idempotency theo checksum/sheet.
- Lưu số dòng, header, cell address, raw value.
- Curriculum bắt đầu ở DRAFT; phiên bản được duyệt sẽ khóa dữ liệu nguồn.
- Có Django Admin để rà soát.
- Theo chỉ đạo của người dùng, 5 curriculum sheets (380 dòng nguồn) đã được kích hoạt: 301 dòng có mã và tên được đưa vào danh mục; 79 dòng tiêu đề/nhóm/tổng kết được giữ lại với trạng thái STRUCTURE.
- Không tự điền tín chỉ còn thiếu. Nguồn Excel giữ nguyên; thay đổi khung chương trình sau này cần nhập thành phiên bản mới.
- Lệnh `activate_imported_curricula` lưu audit event; actor để trống vì môi trường hiện chưa có tài khoản admin.
- Không tự chạy import trên toàn bộ workbook vì mỗi sheet cần config/cột xác nhận riêng.
