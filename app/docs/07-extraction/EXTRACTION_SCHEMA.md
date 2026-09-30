# Extraction schema

`ExtractionRun`: document version, engine/provider, model version, status, raw text, created time.

`ExtractedField`:

- `field_key`: `student_name`, `school_name`, `program`, `course_name`, `credits`, `grade`, `document_date`.
- `raw_value`: giá trị nguyên bản.
- `normalized_value`: giá trị chuẩn hóa nếu có.
- `confidence`: số từ 0 đến 1.
- `page_number`, `evidence_text`, `bounding_box`.
- `review_status`: `AUTO_ACCEPTED`, `NEEDS_REVIEW`, `REJECTED`.

