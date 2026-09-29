from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from gym_tracker.permissions import IsStaffOrAdminInAnyGym
from gym_tracker.utils import get_gym_id_param

from .models import GymMembership, Role, User
from .serializer import GymAdminSerializer, PersonSerializer, StaffMemberSerializer


class _GymScopedUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Usuarios que tienen `role` en alguno de los gimnasios de quien consulta.
    - ?gym=<id> filtra por ese gimnasio (tiene que ser uno al que pertenezcas).
    - En `gyms` de cada usuario solo aparecen los gimnasios que comparte con quien consulta.
    """
    permission_classes = [IsAuthenticated]
    role = None
    # Roles que tiene que tener quien consulta en el gimnasio (None = cualquier rol)
    viewer_roles = None

    def get_queryset(self):
        # Swagger genera el schema con un usuario anónimo
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        viewer = self.request.user
        gym_id = get_gym_id_param(self.request)

        visible_gyms = viewer.memberships.all()
        if self.viewer_roles:
            visible_gyms = visible_gyms.filter(role__in=self.viewer_roles)

        if gym_id:
            if not visible_gyms.filter(gym_id=gym_id).exists():
                raise PermissionDenied("No tienes permiso para ver estos usuarios en este gimnasio.")
            visible_gyms = visible_gyms.filter(gym_id=gym_id)

        shared_memberships = GymMembership.objects.filter(
            gym__in=viewer.memberships.values('gym_id'),
        ).select_related('gym')

        return (
            User.objects.filter(
                memberships__role=self.role,
                memberships__gym__in=visible_gyms.values('gym_id'),
            )
            .distinct()
            .prefetch_related(Prefetch('memberships', queryset=shared_memberships))
            .order_by('email')
        )


class GymAdminViewSet(_GymScopedUserViewSet):
    serializer_class = GymAdminSerializer
    role = Role.ADMIN


class StaffMemberViewSet(_GymScopedUserViewSet):
    serializer_class = StaffMemberSerializer
    role = Role.STAFF


class PersonViewSet(_GymScopedUserViewSet):
    # Los socios no pueden listar a otros socios; solo STAFF o ADMIN de ese gimnasio
    permission_classes = [IsAuthenticated, IsStaffOrAdminInAnyGym]
    viewer_roles = (Role.STAFF, Role.ADMIN)
    serializer_class = PersonSerializer
    role = Role.PERSON
