# Curriculum Data Quality Rules

- Structural differences between workbooks are classified, not silently flattened.
- A course row must retain the source workbook, sheet, and cell/range.
- A missing credit, hour, prerequisite, or assessment value remains unavailable.
- A formula cell is not treated as an approved hardcoded value without recalculation/verification.
- Student-named tabs are flagged as student data and excluded from core curriculum imports.
- `old`, `new`, `sample`, `copy`, and blank sheets require explicit classification.
- Duplicate course codes within one curriculum version are quarantined.
- Similar names do not automatically create equivalence mappings.
