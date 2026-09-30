from rest_framework.permissions import BasePermission

from reviews.models import Role


def user_role(user):
    if user.is_staff:
        return Role.ADMIN
    return getattr(getattr(user, "userprofile", None), "role", None)


class SubmissionPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = user_role(request.user)
        if view.action == "create":
            return role in {Role.ADMIN, Role.SALES}
        return role in {Role.ADMIN, Role.SALES, Role.TEACHER}

    def has_object_permission(self, request, view, obj):
        role = user_role(request.user)
        if role in {Role.ADMIN, Role.TEACHER}:
            return True
        return role == Role.SALES and obj.owner_id == request.user.id

