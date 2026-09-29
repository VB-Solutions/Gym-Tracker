from django.conf import settings
from django.db import models

from .validators import validate_series_data

# ----------------- GIMNASIOS  -----------------

class Gym(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name



# ----------------- EJERCICIOS Y MÚSCULOS -----------------

class Muscle(models.Model):
    muscle_name = models.CharField(max_length=50)
    zone = models.CharField(max_length=50)

    def __str__(self):
        return self.muscle_name

class Exercise(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=200)

    muscle = models.ForeignKey(
        Muscle, 
        on_delete=models.CASCADE, 
        related_name='exercises', 
        blank=True,
        null=True, # Necesario si blank=True en un ForeignKey
        help_text='Muscle of the exercise'
    )

    def __str__(self):
        return self.name

class CustomExercise(Exercise):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name='custom_exercises',
        blank=True,
        null=True,
        help_text='Gym where the custom exercise belongs to',
    )
    video = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class GymStandardExerciseVideo(models.Model):
    """
    Tabla para que cada Gym pueda ponerle su propio video 
    explicativo a un Ejercicio Estándar global.
    """
    gym = models.ForeignKey(
        Gym, 
        on_delete=models.CASCADE, 
        related_name='standard_exercise_videos'
    )
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='gym_videos'
    )
    video = models.URLField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('gym', 'exercise'),
                name='unique_gym_standard_exercise_video',
            ),
        ]

    def __str__(self):
        return f'{self.gym} — {self.exercise}'


# ----------------- RUTINAS Y BLOQUES -----------------

class RoutineQuerySet(models.QuerySet):
    def visible_to(self, user):
        """
        Rutinas que el usuario puede ver, según su rol en cada gimnasio
        (y solo mientras siga perteneciendo a ese gimnasio):
        - Las suyas como socio (person).
        - Las que armó, si es STAFF o ADMIN de ese gimnasio.
        - Todas las del gimnasio, si es ADMIN.
        """
        from users.models import Role

        return self.filter(
            models.Q(person=user, gym__in=user.memberships.values('gym_id'))
            | models.Q(staff=user, gym__in=user.gym_ids_with_role(Role.STAFF, Role.ADMIN))
            | models.Q(gym__in=user.gym_ids_with_role(Role.ADMIN))
        )


class Routine(models.Model):
    objects = RoutineQuerySet.as_manager()

    name = models.CharField(max_length=100)
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name='routines',
    )
    # El rol es por gimnasio (users.GymMembership): se valida en el serializer, no acá
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_routines',
    )
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_routines',
    )

    def __str__(self):
        return self.name


class ExerciseBlock(models.Model):
    # Este bloque debe pertenecer a un día de rutina específico
    routine = models.ForeignKey(
        Routine, 
        on_delete=models.CASCADE, 
        related_name='blocks'
    )
    
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='exercise_blocks'
    )
    day_number = models.IntegerField()

    order = models.SmallIntegerField()
    series_data = models.JSONField(default=list, blank=True, validators=[validate_series_data])

    class Meta:
        ordering = ['routine', 'day_number', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=('routine', 'day_number', 'order'),
                name='unique_routine_day_order_block',
            ),
            models.CheckConstraint(
                condition=models.Q(day_number__gte=1),
                name='exerciseblock_day_number_gte_1',
            ),
            models.CheckConstraint(
                condition=models.Q(order__gte=1),
                name='exerciseblock_order_gte_1',
            ),
        ]

    def __str__(self):
        return f'{self.routine} / día {self.day_number} / {self.exercise}'

    @property
    def gym_id(self):
        # Para que los permisos por gimnasio funcionen igual que con el resto de los objetos
        return self.routine.gym_id

    # Ejemplo de lo que guardarías en series_data desde el Frontend
    # (lo valida validators.validate_series_data):
    # [
    #   {"repe": 12, "peso": 50},
    #   {"repe": 10, "peso": 55},
    #   {"repe": 8, "peso": 60}
    # ]
    
    