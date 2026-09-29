from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import GymMembership, User


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
