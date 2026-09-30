# Curriculum Import Specification

1. Read only classified curriculum sheets.
2. Preserve workbook, sheet, cell/range, and raw value for every imported attribute.
3. Keep student-specific sheets outside core curriculum tables.
4. Keep formulas as raw formula evidence and use cached values only when verified.
5. Keep blank values as missing, not zero.
6. Do not invent course mappings, prerequisite relationships, or effective dates.
7. Reject or quarantine ambiguous duplicate course codes for review.
8. Classify old/new or sample sheets explicitly before import.
9. Import curriculum versions before courses, sections, or prerequisites.
10. Do not import historical student decisions in this phase.

## Workbook-specific observations

- QTKD includes `Tổng quan`, `1.Khung CTDT`, and student sheets.
- Ngôn ngữ Trung includes a curriculum sheet and student sheets with version and hour columns.
- Ngôn ngữ Anh includes a curriculum sheet, a training-plan sheet, and a sample recognition sheet with full/partial recognition columns.
- Đồ họa kỹ thuật số includes current and explicitly labelled new curriculum sheets.
- Du lịch includes structure, training plan, and sample sheets.
