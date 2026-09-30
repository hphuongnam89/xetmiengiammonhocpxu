from django.contrib.auth.models import User
from rest_framework import serializers

from reviews.models import Role, Student, Submission


class MeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")

    def get_role(self, obj):
        if obj.is_staff:
            return Role.ADMIN
        return getattr(getattr(obj, "userprofile", None), "role", None)


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ("id", "student", "owner", "teacher", "status", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate_teacher(self, teacher):
        if teacher and not getattr(getattr(teacher, "userprofile", None), "role", None) == Role.TEACHER:
            raise serializers.ValidationError("Assigned user must have the TEACHER role.")
        return teacher

    def validate_student(self, student):
        if not isinstance(student, Student):
            raise serializers.ValidationError("Invalid student.")
        return student
