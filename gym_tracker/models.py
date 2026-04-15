from django.conf import settings
from django.db import models

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

class Routine(models.Model):
    name = models.CharField(max_length=100)
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name='routines',
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_routines',
        limit_choices_to={'role': 'STAFF'},
    )
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_routines',
        limit_choices_to={'role': 'PERSON'},
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
    series_data = models.JSONField(default=list)

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

    # Ejemplo de lo que guardarías en series_data desde el Frontend:
    # [
    #   {"repe": 12, "peso": 50},
    #   {"repe": 10, "peso": 55},
    #   {"repe": 8, "peso": 60}
    # ]
    
    