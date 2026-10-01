# API contract

Recommendation run phải tham chiếu `submission_id`, `rule_version_id`, curriculum version đích và input snapshot đã xác nhận từ server; không nhận điểm/evidence tùy ý từ caller.

Mỗi item phải có `course_code`, `recommendation`, `evidence`, `reason`, `confidence`, `needs_human_review`.

Chỉ rule đã duyệt, có `definition.rules` và cổng xác nhận chủ học thuật mới được chạy. Mapping thiếu hoặc nhập nhằng phải ở trạng thái cần giảng viên rà soát.

Không có endpoint nào được chuyển recommendation thành final decision nếu chưa có teacher decision. API từ chối quyết định trên run đã bị run mới hơn thay thế.

