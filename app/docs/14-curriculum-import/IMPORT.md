# Import procedure

Management command `import_curriculum` nhận workbook và JSON config gồm program code/name, sheet, version label, header row và map tên cột nguồn. Chạy `--dry-run` trước. Import lưu SHA-256 workbook, filename, sheet, số dòng và cell evidence. Formula được giữ nguyên dạng raw text; không lấy cached formula value để suy diễn credits. Không có quan hệ equivalency nào được tạo tự động.
