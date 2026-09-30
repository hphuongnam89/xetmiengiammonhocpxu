# Migration plan

1. Tạo schema trên database mới hoặc migration mở rộng; không sửa/xoá cột đang chứa dữ liệu nguồn.
2. Thêm cột mới ở trạng thái nullable hoặc có default an toàn.
3. Deploy code tương thích cả schema cũ và mới.
4. Backfill theo lô nhỏ, idempotent, có checkpoint và log lỗi.
5. Kiểm tra số lượng, khóa ngoại, checksum và sample dữ liệu.
6. Chỉ sau khi kiểm chứng mới thêm constraint bắt buộc.
7. Đánh dấu trường/record cũ là legacy thay vì xoá.

## Quy tắc rollback

- Migration schema có reverse migration khi khả thi.
- Migration dữ liệu phải có snapshot/checkpoint trước khi chạy.
- Không rollback bằng cách xoá toàn bộ dữ liệu mới; dùng trạng thái hoặc migration bù.
- Mọi migration production cần peer review, dry-run và biên bản kết quả.

## Dữ liệu import lịch sử

- Giữ file gốc, checksum và manifest.
- Import vào trạng thái `IMPORTED_REVIEW` trước khi `APPROVED`.
- Record không đủ bằng chứng không được dùng để tự động ra quyết định.

