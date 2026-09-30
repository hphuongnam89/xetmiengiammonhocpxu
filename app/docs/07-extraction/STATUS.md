# Phase 7 Status

## Đã triển khai

- `ExtractionRun` và `ExtractedField` có raw value, normalized value, confidence, evidence và review status.
- Endpoint `POST /api/v1/documents/{id}/extract/`.
- PDF text-layer adapter bằng pypdf.
- Ảnh/PDF scan chưa có text layer được đánh dấu `NEEDS_REVIEW`.
- Parser chỉ lấy giá trị có nhãn, không tự bịa trường thiếu.
- Migration `0003_extractionrun_extractedfield`.
- OCR/extraction fields and review status are covered by the current API test suite.

## Chưa đóng toàn bộ phase

- Chưa kiểm chứng PDF scan nhiều bố cục.
- Chưa truyền extraction vào rule engine.

## Cập nhật

- Có màn hình rà soát OCR theo tài liệu; người có quyền mở bản gốc, sửa/xác nhận/loại trường hoặc thêm trường thiếu với trang và bằng chứng.
- Raw OCR không bị ghi đè; field review và manual additions được audit, manual confirmation có status riêng. Extraction chưa được nối tự động vào rule engine.
