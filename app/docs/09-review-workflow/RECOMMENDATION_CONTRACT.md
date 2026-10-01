# Recommendation contract

`POST /api/v1/submissions/{id}/recommendations/`

The request includes `rule_version_id`, `curriculum_version_id`, `idempotency_key`, and `course_row_ids`. It does not accept course grades, credits, mappings, evidence, or target course codes from the caller. Rows must already exist on the submission and link explicitly assembled extracted fields.

Each source field must have `HUMAN_ACCEPTED` status and source evidence text or a page reference. Course name, optional source code, grade, and credits must come from one extraction run on the same submission. Grade and credits must be finite numeric values. The target must be a coded, approved course in the explicitly selected approved curriculum. The curriculum program must match the student's program when the latter is known.

Only a rule with `APPROVED` status, structured `definition.rules`, and a recorded academic owner review (`verified`, `reviewer`, and `note`) may run. Only a unique, approved mapping with the same academic review gate provides a content match. Missing or ambiguous mapping stays in human review. The deterministic evaluator remains limited; this gate does not mean it executes every rule definition.

Each `RecommendationItem` stores a snapshot of confirmed field values, raw values, evidence text, review status, extraction run, document checksum, source page, chosen target course, curriculum version, and any approved mapping reference. The `RecommendationRun` stores the rule and curriculum versions. One run per submission is marked current; a new run supersedes it, and decisions cannot be made on a superseded run. Teacher decisions remain separate from the recommendation.

Repeating a request with the same submission/key and identical rule, curriculum, and course rows returns the existing run. Reusing the key for different inputs returns a conflict/validation error. A caller cannot inject arbitrary `items`.
