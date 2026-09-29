from rest_framework import permissions

from users.models import Role

'----------- Permissions -------------'
# El rol de un usuario es POR GIMNASIO (users.GymMembership), por eso estos permisos
# miran el gimnasio del objeto. Al CREAR todavía no hay objeto: ese chequeo se hace
# en perform_create con utils.require_gym_role().

class IsGymStaffOrAdminOrReadOnly(permissions.BasePermission):
    """
    Para objetos con `gym`: cualquiera que llegue al objeto lo puede leer
    (el queryset ya filtra por gimnasio), pero solo STAFF o ADMIN de ese
    gimnasio lo pueden modificar o borrar.
    """
    message = "Solo STAFF o ADMIN de este gimnasio pueden hacer esto."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.has_gym_role(obj.gym_id, Role.STAFF, Role.ADMIN)


class _HasRoleInAnyGym(permissions.BasePermission):
    """El usuario tiene alguno de `roles` en al menos un gimnasio."""
    roles = ()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.memberships.filter(role__in=self.roles).exists()
        )


class IsStaffOrAdminInAnyGym(_HasRoleInAnyGym):
    roles = (Role.STAFF, Role.ADMIN)
    message = "Solo STAFF o ADMIN pueden acceder a este recurso."


class IsAdminInAnyGym(_HasRoleInAnyGym):
    roles = (Role.ADMIN,)
    message = "Solo un ADMIN de gimnasio puede acceder a este recurso."

'-----------------------------------'
