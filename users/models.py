from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser ,  BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio para crear un usuario')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Role(models.TextChoices):
    """Rol de un usuario DENTRO de un gimnasio (ver GymMembership)."""
    ADMIN = 'ADMIN', 'Gym Admin'
    STAFF = 'STAFF', 'Staff/Trainer'
    PERSON = 'PERSON', 'Socio/Cliente'


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    # RELACIÓN N a N: Un usuario puede estar en varios gimnasios
    # y un gimnasio tiene muchos usuarios. El rol de cada uno se guarda en GymMembership.
    gyms = models.ManyToManyField(
        'gym_tracker.Gym',
        through='GymMembership',
        related_name='users',
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def role_in(self, gym):
        """Rol del usuario en ese gimnasio (instancia o id), o None si no pertenece."""
        membership = self.memberships.filter(gym=gym).first()
        return membership.role if membership else None

    def has_gym_role(self, gym, *roles):
        """True si el usuario tiene alguno de esos roles en el gimnasio (instancia o id)."""
        return self.memberships.filter(gym=gym, role__in=roles).exists()

    def gym_ids_with_role(self, *roles):
        """Subquery con los ids de los gimnasios donde el usuario tiene alguno de esos roles."""
        return self.memberships.filter(role__in=roles).values('gym_id')


class GymMembership(models.Model):
    """Pertenencia de un usuario a un gimnasio, con su rol en ese gimnasio."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    gym = models.ForeignKey(
        'gym_tracker.Gym',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PERSON)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'gym'), name='unique_user_gym_membership'),
        ]

    def __str__(self):
        return f'{self.user} — {self.gym} ({self.role})'
