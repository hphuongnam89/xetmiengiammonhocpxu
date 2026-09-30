# Mapping versioning

`RuleMappingVersion` lưu mapping code/version, source course, target course, criteria JSON, source reference, trạng thái, người tạo và người duyệt. Django Admin tạo draft, approve bằng action, retire version cũ; approve/retire ghi AuditEvent. Version number tự tăng theo mapping code.
