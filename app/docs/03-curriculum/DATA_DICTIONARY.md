# Curriculum Data Dictionary

## Program

`program_code`, `program_name`, `source_workbook`, `source_sheet`, `raw_name`.

## Curriculum Version

`version_id`, `program_code`, `raw_title`, `cohort_text`, `effective_from`, `effective_to`, `status`, `source_evidence_id`.

Dates remain null when the source does not provide a verified date.

## Curriculum Section

`section_id`, `version_id`, `raw_label`, `section_order`, `section_type`, `source_evidence_id`.

## Course

`course_id`, `version_id`, `raw_stt`, `raw_code`, `normalized_code`, `raw_name`, `normalized_name`, `credits`, `theory_hours`, `practice_hours`, `self_study_hours`, `course_type`, `assessment`, `source_evidence_id`.

## Course Prerequisite

`course_id`, `raw_prerequisite`, `relation_type`, `related_raw_code`, `source_evidence_id`.

## Source Cell Evidence

`source_file_id`, `workbook_path`, `sheet_name`, `cell_or_range`, `raw_value`, `extraction_method`, `review_status`.

Raw values must remain available beside normalized values.
