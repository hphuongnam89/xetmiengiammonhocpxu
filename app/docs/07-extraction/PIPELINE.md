# Pipeline

1. Load immutable `DocumentVersion`.
2. Kiểm tra MIME và checksum.
3. PDF text layer dùng parser; ảnh/PDF scan đi qua OCR adapter ở bước kế tiếp.
4. Parser trả raw text và field candidates.
5. Chuẩn hóa giá trị, gắn page/evidence/confidence.
6. Lưu `ExtractionRun` và `ExtractedField`.
7. Trường dưới ngưỡng hoặc mâu thuẫn chuyển sang human review.

