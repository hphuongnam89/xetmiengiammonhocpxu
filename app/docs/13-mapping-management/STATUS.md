# Phase 13 Status

- Có model versioned mapping và unique constraint theo code/version.
- Admin có tạo/sửa draft, approve, retire; audit actor và version.
- Nội dung mapping approved bị khóa; sửa phải tạo version mới.
- Sửa quyết định hồ sơ vẫn ở TeacherDecision riêng.
- Recommendation evaluator dùng mapping approved theo cặp môn nguồn/đích; không có mapping thì yêu cầu human review.
