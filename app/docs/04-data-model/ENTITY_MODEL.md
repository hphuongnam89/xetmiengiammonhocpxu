# Entity model

## Identity and access

- `User`: tài khoản đăng nhập, trạng thái, thời gian tạo.
- `Role`: `ADMIN`, `SALES`, `TEACHER`.
- `UserRole`: liên kết user-role; không hard-code quyền trong giao diện.

## Academic source

- `Program`: ngành/chương trình.
- `CurriculumVersion`: phiên bản khung chương trình, nguồn và ngày hiệu lực.
- `CurriculumSection`: nhóm kiến thức.
- `Course`: mã, tên, tín chỉ, tiết, loại học phần, điều kiện tiên quyết.
- `CoursePrerequisite`: quan hệ tiên quyết.
- `SourceEvidence`: workbook/sheet/cell/range/page và giá trị raw.

## Student and documents

- `Student`: mã hồ sơ, thông tin định danh tối thiểu.
- `Submission`: hồ sơ xét, sales phụ trách, chương trình, trạng thái workflow.
- `Document`: loại tài liệu, tên file, checksum, storage key.
- `DocumentVersion`: file bất biến, MIME, kích thước, checksum, thời điểm tải lên.
- `ExtractedField`: trường OCR/extraction, giá trị, confidence, vị trí và model version.

## Rules and decisioning

- `Rule`: mã rule nghiệp vụ.
- `RuleVersion`: nội dung, nguồn, trạng thái `DRAFT/APPROVED/RETIRED`.
- `RecommendationRun`: một lần xử lý, model/provider, prompt hash, token/cost, trạng thái.
- `RecommendationItem`: đề xuất cho từng môn, evidence, confidence, lý do; bất biến sau khi tạo.
- `TeacherDecision`: kết quả cuối, người duyệt, lý do, thời điểm, phiên bản chỉnh sửa.

## Operations

- `Notification`: người nhận, sự kiện, trạng thái đọc/gửi.
- `AuditEvent`: actor, action, entity, before/after hash, correlation id.
- `AIUsageEvent`: provider/model, operation, input/output tokens, cost, request id, thời gian.

## Quan hệ chính

`Submission -> Student`, `Submission -> DocumentVersion`, `Submission -> RecommendationRun`, `RecommendationRun -> RecommendationItem`, `RecommendationItem -> TeacherDecision`.

Mọi liên kết học thuật đi qua `SourceEvidence`; mọi đề xuất đi qua `RuleVersion` và `RecommendationRun`.

