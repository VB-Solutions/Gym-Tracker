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
