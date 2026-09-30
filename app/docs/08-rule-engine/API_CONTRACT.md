# API contract

Recommendation run phải tham chiếu `submission_id`, `rule_version_id`, input snapshot và engine version.

Mỗi item phải có `course_code`, `recommendation`, `evidence`, `reason`, `confidence`, `needs_human_review`.

Không có endpoint nào được chuyển recommendation thành final decision nếu chưa có teacher decision.

