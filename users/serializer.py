from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import GymMembership, Role, User


class UserGymSerializer(serializers.ModelSerializer):
    """Un gimnasio del usuario con su rol ahí: {"id", "name", "role"}."""

    id = serializers.IntegerField(source='gym.id', read_only=True)
    name = serializers.CharField(source='gym.name', read_only=True)

    class Meta:
        model = GymMembership
        fields = ('id', 'name', 'role')


_USER_READ_FIELDS = (
    'id',
    'email',
    'first_name',
    'last_name',
    'is_active',
    'date_joined',
    'gyms',
)


class UserReadSerializer(serializers.ModelSerializer):
    """Safe fields for listing user profiles (no password or permissions)."""

    gyms = UserGymSerializer(source='memberships', many=True, read_only=True)

    class Meta:
        model = User
        fields = _USER_READ_FIELDS


class GymAdminSerializer(UserReadSerializer):
    """Gym admins (rol ADMIN en algún gimnasio)."""


class StaffMemberSerializer(UserReadSerializer):
    """Trainers / staff (rol STAFF en algún gimnasio)."""


class PersonSerializer(UserReadSerializer):
    """Members / clients (rol PERSON en algún gimnasio)."""


class UserSerializer(UserReadSerializer):
    """Backward-compatible name for the shared read shape."""


class MeSerializer(UserReadSerializer):
    """El usuario logueado: puede editar su nombre; el email y los gimnasios son de solo lectura."""

    class Meta(UserReadSerializer.Meta):
        read_only_fields = ('id', 'email', 'is_active', 'date_joined')


class MemberUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')


class GymMembershipSerializer(serializers.ModelSerializer):
    """
    Membresía de un gimnasio, para que su ADMIN gestione quién está y con qué rol.
    - Al crear: {gym, email, role}. El usuario tiene que estar registrado.
    - Al editar: solo se puede cambiar el rol.
    """

    user = MemberUserSerializer(read_only=True)
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = GymMembership
        fields = ('id', 'gym', 'user', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar no se puede mover la membresía a otro gimnasio ni a otro usuario
        if self.instance is not None:
            self.fields['gym'].read_only = True
            self.fields.pop('email')

    def validate_gym(self, gym):
        # Antes de mirar el email: así solo un ADMIN puede averiguar qué emails están registrados
        if not self.context['request'].user.has_gym_role(gym, Role.ADMIN):
            raise PermissionDenied("Solo un ADMIN de este gimnasio puede sumar miembros.")
        return gym

    def validate(self, attrs):
        if self.instance is not None:
            return attrs

        user = User.objects.filter(email__iexact=attrs.pop('email')).first()
        if user is None:
            raise serializers.ValidationError(
                {"email": "No hay ningún usuario con este email. Primero tiene que registrarse."}
            )
        if GymMembership.objects.filter(user=user, gym=attrs['gym']).exists():
            raise serializers.ValidationError({"email": "Este usuario ya pertenece al gimnasio."})

        attrs['user'] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """Alta pública de un usuario. Queda sin gimnasios hasta que un ADMIN lo sume a uno."""

    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return email

    def validate(self, attrs):
        # Mismas reglas de contraseña que el resto de Django (largo, comunes, parecida al email...)
        user = User(**{field: value for field, value in attrs.items() if field != 'password'})
        try:
            validate_password(attrs['password'], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
