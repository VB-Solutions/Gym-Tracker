from rest_framework import serializers

from gym_tracker.serializer import GymSerializer

from .models import User

_USER_READ_FIELDS = (
    'id',
    'email',
    'first_name',
    'last_name',
    'role',
    'is_active',
    'date_joined',
    'gyms',
)


class UserReadSerializer(serializers.ModelSerializer):
    """Safe fields for listing user profiles (no password or permissions)."""

    gyms = GymSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = _USER_READ_FIELDS


class GymAdminSerializer(UserReadSerializer):
    """Gym admins (`User.Role.ADMIN`). Use with a queryset filtered by that role."""


class StaffMemberSerializer(UserReadSerializer):
    """Trainers / staff (`User.Role.STAFF`)."""


class PersonSerializer(UserReadSerializer):
    """Members / clients (`User.Role.PERSON`)."""


class UserSerializer(UserReadSerializer):
    """Backward-compatible name for the shared read shape."""
