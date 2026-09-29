from django.db.models import Prefetch
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from gym_tracker.permissions import IsStaffOrAdminInAnyGym
from gym_tracker.utils import get_gym_id_param

from .models import GymMembership, Role, User
from .serializer import (
    GymAdminSerializer,
    MeSerializer,
    PersonSerializer,
    RegisterSerializer,
    StaffMemberSerializer,
)


# ----------------- AUTENTICACIÓN (JWT) -----------------

class LoginView(TokenObtainPairView):
    """
    POST /users/auth/login/ {email, password} -> {access, refresh}.
    Después mandar `Authorization: Bearer <access>` en cada pedido.
    """
    throttle_scope = 'auth'


class RefreshView(TokenRefreshView):
    """POST /users/auth/refresh/ {refresh} -> {access} nuevo cuando vence el anterior."""
    throttle_scope = 'auth'


class RegisterView(generics.CreateAPIView):
    """
    POST /users/auth/register/ {email, password, first_name, last_name}.
    Crea el usuario sin gimnasios: un ADMIN lo suma a su gimnasio con un rol.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET /users/me/ -> Datos del usuario logueado con sus gimnasios y su rol en cada uno.
    PATCH /users/me/ -> Edita nombre y apellido.
    """
    serializer_class = MeSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return (
            User.objects
            .prefetch_related(Prefetch('memberships', queryset=GymMembership.objects.select_related('gym')))
            .get(pk=self.request.user.pk)
        )


# ----------------- USUARIOS POR ROL -----------------


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
