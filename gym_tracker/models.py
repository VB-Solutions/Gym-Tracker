from dis import stack_effect
from django.db import models
from django.contrib.auth.models import AbstractUser

#modelos para cargar la base de datos, cada clase es una tabla, cada atributo es un campo de la tabla
class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    done = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title


class Gym (models.Model):
    name = models.CharField(max_length = 30)


class User (AbstractUser):
    class Role (models.TextChoices):
        ADMIN = 'ADMIN', 'Gym Admin'
        STAFF = 'STAFF', 'Staff/Trainer'
        PERSON = 'PERSON', 'Person/Client'
        
    role = models.CharField(max_length = 15 , choices = Role.choices , default=Role.PERSON)
    gyms = models.ManyToManyField(
        'Gym', 
        related_name='users', # Para traer todos los usuarios de un gym, los llamo con users
        blank=True,
        help_text="Gyms of the user."
    )
    
class Muscle (models.Model):
    muscle_name = models.CharField(max_length = 50)
    zone = models.CharField(max_length = 50)

class Exercise (models.Model):
    
    name = models.CharField(max_length = 50)
    muscle = models.ForeignKey('Muscle',related_name='exercises',blank=True,help_text='Muscle of the exercise');
    
class ExerciseBlock(models.Model):
    Exercise = models.ForeignKey('Exercise', related_name='exercise_blocks',blank=True,help_text='Exercise of the block')
    series_data = models.JSONField(default=list)
    day_number = models.SmallIntegerField()
    order = models.SmallIntegerField()
    
    


    