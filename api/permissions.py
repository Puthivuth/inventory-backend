from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    """
    Allows access only to users with the 'administrator' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'administrator')

class IsManager(BasePermission):
    """
    Allows access only to users with the 'manager' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'manager')
    
class IsStaff(BasePermission):
    """
    Allows access only to users with the 'staff' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'staff')
    
class IsAdminOrManager(BasePermission):
    """
    Allows access to users with either 'administrator' or 'manager' roles.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                    (request.user.role == 'administrator' or request.user.role == 'manager'))
        
class IsManagerOrReadOnly(BasePermission):
    """
    Allows read-only access to any authenticated user, 
    but write access only to 'administrator' or 'manager' roles.
    """
    def has_permission(self, request, view):
        # Allow read-only access for any authenticated user (e.g., staff)
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write access only to administrators or managers
        return bool(request.user and request.user.is_authenticated and 
                    (request.user.role == 'administrator' or request.user.role == 'manager'))