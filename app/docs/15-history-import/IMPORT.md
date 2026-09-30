# Import procedure

Management command `import_historical_reviews` dùng config JSON chỉ rõ sheet, header row, cột mã môn/tên môn/quyết định và decision map. Chạy dry-run trước. Import chỉ lấy các trường được cấu hình, hash workbook và optional student key; mọi row ở PENDING kể cả khi decision map nhận diện được. Import lặp idempotent theo hash/sheet/row.

Với workbook hồ sơ QTKD nhiều sheet có cột `Công nhận hoàn toàn`/`Công nhận 1 phần`, dùng `stage_historical_workbook` cùng `app/config/import-manifests/historical-qtkd-16-students.json`. Lệnh mặc định chỉ preview; `--apply` mới ghi. Chỉ sheet khớp đủ tiêu đề mới được xử lý, tên sheet người học được thay bằng số thứ tự, và mọi dòng vẫn PENDING.
