from rest_framework import permissions


class UserPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True

        if request.method == 'POST':
            return request.user is None

        return request.user is not None

    def has_object_permission(self, request, view, obj):
        return request.user is not None and obj.id == request.user.id
