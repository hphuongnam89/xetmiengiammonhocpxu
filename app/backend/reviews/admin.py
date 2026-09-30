from django.contrib import admin, messages
from django.utils import timezone

from .models import (AuditEvent, Course, CurriculumVersion, CurriculumVersionStatus,
    HistoricalDecision, HistoricalDecisionStatus, MappingStatus, RuleMappingVersion,
    RuleVersion, UserProfile)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


@admin.register(RuleMappingVersion)
class RuleMappingVersionAdmin(admin.ModelAdmin):
    list_display = ("mapping_code", "version", "source_course", "target_course_code", "status", "created_by", "approved_by")
    list_filter = ("status",)
    search_fields = ("mapping_code", "source_course", "target_course_code", "source_reference")
    readonly_fields = ("version", "status", "created_by", "approved_by", "created_at", "approved_at")
    actions = ("approve_drafts", "retire_selected")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == MappingStatus.APPROVED:
            return self.readonly_fields + ("mapping_code", "source_course", "target_course_code", "mapping_data", "source_reference")
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            latest = RuleMappingVersion.objects.filter(mapping_code=obj.mapping_code).order_by("-version").first()
            obj.version = (latest.version + 1) if latest else 1
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Approve selected mapping drafts")
    def approve_drafts(self, request, queryset):
        approved = skipped = 0
        for mapping in queryset.filter(status=MappingStatus.DRAFT):
            review = mapping.mapping_data.get("academic_owner_review", {})
            if not (review.get("verified") is True and review.get("reviewer") and review.get("note")):
                skipped += 1
                continue
            mapping.status = MappingStatus.APPROVED
            mapping.approved_by = request.user
            mapping.approved_at = timezone.now()
            mapping.save()
            AuditEvent.objects.create(actor=request.user, action="RULE_MAPPING_APPROVED", entity_type="RuleMappingVersion",
                entity_id=str(mapping.id), payload={"mapping_code": mapping.mapping_code, "version": mapping.version,
                                                    "academic_reviewer": review["reviewer"]})
            approved += 1
        if skipped:
            self.message_user(request, f"Đã duyệt {approved}; bỏ qua {skipped} mapping chưa có xác nhận học thuật.", level=messages.WARNING)

    @admin.action(description="Retire selected mapping versions")
    def retire_selected(self, request, queryset):
        for mapping in queryset.exclude(status=MappingStatus.RETIRED):
            mapping.status = MappingStatus.RETIRED
            mapping.save()
            AuditEvent.objects.create(actor=request.user, action="RULE_MAPPING_RETIRED", entity_type="RuleMappingVersion",
                entity_id=str(mapping.id), payload={"mapping_code": mapping.mapping_code, "version": mapping.version})


@admin.register(RuleVersion)
class RuleVersionAdmin(admin.ModelAdmin):
    list_display = ("rule_code", "version", "status", "source_reference", "created_at")
    list_filter = ("status",)
    search_fields = ("rule_code", "source_reference")
    readonly_fields = ("status", "created_at", "approved_by", "approved_at")
    actions = ("approve_verified_drafts", "retire_selected")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == RuleStatus.APPROVED:
            return tuple(field.name for field in self.model._meta.fields)
        return self.readonly_fields

    @admin.action(description="Approve selected rule drafts after academic review")
    def approve_verified_drafts(self, request, queryset):
        approved = skipped = 0
        for rule in queryset.filter(status=RuleStatus.DRAFT):
            review = rule.definition.get("academic_owner_review", {})
            if not (rule.definition.get("rules") and review.get("verified") is True
                    and review.get("reviewer") and review.get("note")):
                skipped += 1
                continue
            rule.status = RuleStatus.APPROVED
            rule.approved_by = request.user
            rule.approved_at = timezone.now()
            rule.save()
            AuditEvent.objects.create(actor=request.user, action="RULE_VERSION_APPROVED", entity_type="RuleVersion",
                entity_id=str(rule.id), payload={"rule_code": rule.rule_code, "version": rule.version,
                                                 "academic_reviewer": review["reviewer"]})
            approved += 1
        if skipped:
            self.message_user(request, f"Đã duyệt {approved}; bỏ qua {skipped} rule chưa có rule có cấu trúc hoặc xác nhận học thuật.",
                              level=messages.WARNING)

    @admin.action(description="Retire selected approved rules")
    def retire_selected(self, request, queryset):
        for rule in queryset.filter(status=RuleStatus.APPROVED):
            rule.status = RuleStatus.RETIRED
            rule.save()
            AuditEvent.objects.create(actor=request.user, action="RULE_VERSION_RETIRED", entity_type="RuleVersion",
                entity_id=str(rule.id), payload={"rule_code": rule.rule_code, "version": rule.version})


@admin.register(CurriculumVersion)
class CurriculumVersionAdmin(admin.ModelAdmin):
    list_display = ("program", "version_label", "source_sheet", "status", "approved_by")
    list_filter = ("status", "program")
    readonly_fields = ("source_sha256", "imported_at", "status", "approved_by", "approved_at")
    actions = ("approve_curricula",)

    @admin.action(description="Approve selected curriculum versions")
    def approve_curricula(self, request, queryset):
        for curriculum in queryset.filter(status=CurriculumVersionStatus.DRAFT):
            curriculum.status = CurriculumVersionStatus.APPROVED
            curriculum.approved_by = request.user
            curriculum.approved_at = timezone.now()
            curriculum.save()
            AuditEvent.objects.create(actor=request.user, action="CURRICULUM_APPROVED", entity_type="CurriculumVersion",
                entity_id=str(curriculum.id), payload={"program": curriculum.program_id, "version": curriculum.version_label})


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("raw_code", "raw_name", "curriculum", "review_status", "source_row")
    list_filter = ("review_status", "curriculum__program")
    search_fields = ("raw_code", "raw_name")
    readonly_fields = ("source_row", "source_cells")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.curriculum.status == CurriculumVersionStatus.APPROVED:
            return tuple(field.name for field in self.model._meta.fields)
        return self.readonly_fields


@admin.register(HistoricalDecision)
class HistoricalDecisionAdmin(admin.ModelAdmin):
    list_display = ("program_code", "course_code", "decision_raw", "decision", "status", "source_sheet", "source_row", "reviewed_by")
    list_filter = ("status", "program_code", "decision")
    search_fields = ("course_code", "course_name", "source_file", "source_sheet")
    readonly_fields = ("source_sha256", "source_file", "source_sheet", "source_row", "source_key_hash", "source_cells",
                       "status", "reviewed_by", "reviewed_at")
    actions = ("approve_precedents", "reject_precedents")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == HistoricalDecisionStatus.APPROVED:
            return tuple(field.name for field in self.model._meta.fields)
        return self.readonly_fields

    @admin.action(description="Approve normalized historical decisions as precedents")
    def approve_precedents(self, request, queryset):
        for record in queryset.filter(status=HistoricalDecisionStatus.PENDING).exclude(decision=""):
            record.status = HistoricalDecisionStatus.APPROVED
            record.reviewed_by = request.user
            record.reviewed_at = timezone.now()
            record.save()
            AuditEvent.objects.create(actor=request.user, action="HISTORICAL_DECISION_APPROVED", entity_type="HistoricalDecision",
                entity_id=str(record.id), payload={"course_code": record.course_code, "decision": record.decision})

    @admin.action(description="Reject selected historical decisions")
    def reject_precedents(self, request, queryset):
        for record in queryset.filter(status=HistoricalDecisionStatus.PENDING):
            record.status = HistoricalDecisionStatus.REJECTED
            record.reviewed_by = request.user
            record.reviewed_at = timezone.now()
            record.save()
