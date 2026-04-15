from rest_framework import viewsets

from .models import User
from .serializer import GymAdminSerializer, PersonSerializer, StaffMemberSerializer


class _GymScopedUserViewSet(viewsets.ReadOnlyModelViewSet):
    role = None

    def get_queryset(self):
        qs = User.objects.filter(role=self.role).prefetch_related('gyms').order_by('email')
        gym_id = self.request.query_params.get('gym')
        if gym_id is not None and gym_id != '':
            qs = qs.filter(gyms__id=gym_id).distinct()
        return qs


class GymAdminViewSet(_GymScopedUserViewSet):
    serializer_class = GymAdminSerializer
    role = User.Role.ADMIN


class StaffMemberViewSet(_GymScopedUserViewSet):
    serializer_class = StaffMemberSerializer
    role = User.Role.STAFF


class PersonViewSet(_GymScopedUserViewSet):
    serializer_class = PersonSerializer
    role = User.Role.PERSON
