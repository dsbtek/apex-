from rest_framework.permissions import BasePermission

class IsActiveAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active


class IsActiveAuthenticatedAdmin(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active and request.user.Role_id == 4


#define super admin access
#define product admin access