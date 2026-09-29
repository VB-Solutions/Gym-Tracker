from django.db.models import Prefetch
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from gym_tracker.permissions import IsAdminInAnyGym, IsStaffOrAdminInAnyGym
from gym_tracker.utils import get_gym_id_param

from .models import GymMembership, Role, User
from .serializer import (
    GymAdminSerializer,
    GymMembershipSerializer,
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


# ----------------- MEMBRESÍAS (gestión del ADMIN) -----------------

class GymMembershipViewSet(viewsets.ModelViewSet):
    """
    El ADMIN de un gimnasio gestiona quién pertenece y con qué rol.
    - GET /users/memberships/ -> Membresías de los gimnasios que administrás (?gym=<id> filtra).
    - POST /users/memberships/ {gym, email, role} -> Suma a un usuario ya registrado.
    - PATCH /users/memberships/<id>/ {role} -> Cambia el rol.
    - DELETE /users/memberships/<id>/ -> Saca al usuario del gimnasio.
    El gimnasio siempre tiene que quedar con al menos un ADMIN.
    """
    serializer_class = GymMembershipSerializer
    permission_classes = [IsAuthenticated, IsAdminInAnyGym]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GymMembership.objects.none()

        user = self.request.user
        qs = (
            GymMembership.objects
            .filter(gym__in=user.gym_ids_with_role(Role.ADMIN))
            .select_related('user', 'gym')
            .order_by('gym_id', 'user__email')
        )

        if self.action == 'list':
            gym_id = get_gym_id_param(self.request)
            if gym_id:
                if not user.has_gym_role(gym_id, Role.ADMIN):
                    raise PermissionDenied("Solo un ADMIN de este gimnasio puede ver sus miembros.")
                qs = qs.filter(gym_id=gym_id)

        return qs

    def perform_update(self, serializer):
        self._ensure_gym_keeps_an_admin(serializer.instance, serializer.validated_data.get('role'))
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_gym_keeps_an_admin(instance, new_role=None)
        instance.delete()

    def _ensure_gym_keeps_an_admin(self, membership, new_role):
        if membership.role != Role.ADMIN or new_role == Role.ADMIN:
            return
        other_admins = GymMembership.objects.filter(
            gym_id=membership.gym_id, role=Role.ADMIN,
        ).exclude(pk=membership.pk)
        if not other_admins.exists():
            raise ValidationError("El gimnasio tiene que quedar con al menos un ADMIN.")


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
