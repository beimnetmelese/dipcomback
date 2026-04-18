from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in {'admin', 'staff'})


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'admin')


class ReadOnlyOrAdminStaff(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        return bool(user and user.is_authenticated and user.role in {'admin', 'staff'})