from rest_framework import permissions

'----------- Permissions -------------'
class IsStaffRole(permissions.BasePermission):
    """
    Permiso personalizado que solo deja pasar a los usuarios 
    cuyo rol sea 'STAFF'.
    """
    def has_permission(self, request, view):
        # Verificamos si el usuario está autenticado y tiene el rol correcto
        return bool(request.user and request.user.is_authenticated and request.user.role == 'STAFF')

class IsPersonRole(permissions.BasePermission):
    """
    Permiso personalizado que solo deja pasar a los usuarios 
    cuyo rol sea 'PERSON'.
    """
    def has_permission(self, request, view):
        # Verificamos si el usuario está autenticado y tiene el rol correcto
        return bool(request.user and request.user.is_authenticated and request.user.role == 'PERSON')
    
class IsAdminRole(permissions.BasePermission):
    """
    Permiso personalizado que solo deja pasar a los usuarios 
    cuyo rol sea 'ADMIN'.
    """
    def has_permission(self, request, view):
        # Verificamos si el usuario está autenticado y tiene el rol correcto
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

'-----------------------------------'