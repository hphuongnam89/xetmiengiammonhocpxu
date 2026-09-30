# Recommendation contract

`POST /api/v1/submissions/{id}/recommendations/`

Input gồm `rule_version_id`, `idempotency_key` và danh sách môn có `course_code`, `prior_course`, `prior_grade`, `prior_credits`, `evidence`. Không tin `content_match` do client gửi. Engine chỉ xác nhận khớp khi tìm thấy RuleMappingVersion đã APPROVED cho cặp môn nguồn/đích.

Output lưu `RecommendationRun` và `RecommendationItem`, bao gồm recommendation, rationale, confidence và evidence snapshot.

Run lặp cùng submission + idempotency key phải trả lại run cũ, không tạo bản sao.
