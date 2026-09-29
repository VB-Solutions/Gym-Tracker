from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from gym_tracker.permissions import IsAdminRole, IsStaffRole
from gym_tracker.utils import get_gym_id_param

from .models import User
from .serializer import GymAdminSerializer, PersonSerializer, StaffMemberSerializer


class _GymScopedUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo se ven los usuarios que comparten al menos un gimnasio con quien consulta.
    - ?gym=<id> filtra por ese gimnasio (tiene que ser uno al que pertenezcas).
    """
    permission_classes = [IsAuthenticated]
    role = None

    def get_queryset(self):
        # Swagger genera el schema con un usuario anónimo
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        gym_id = get_gym_id_param(self.request)
        gyms = [gym_id] if gym_id else self.request.user.gyms.all()

        return (
            User.objects.filter(role=self.role, gyms__in=gyms)
            .distinct()
            .prefetch_related('gyms')
            .order_by('email')
        )


class GymAdminViewSet(_GymScopedUserViewSet):
    serializer_class = GymAdminSerializer
    role = User.Role.ADMIN


class StaffMemberViewSet(_GymScopedUserViewSet):
    serializer_class = StaffMemberSerializer
    role = User.Role.STAFF


class PersonViewSet(_GymScopedUserViewSet):
    # Los socios no pueden listar a otros socios; solo STAFF o ADMIN
    permission_classes = [IsAuthenticated, IsStaffRole | IsAdminRole]
    serializer_class = PersonSerializer
    role = User.Role.PERSON
