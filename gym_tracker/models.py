from django.db import models

#modelos para cargar la base de datos, cada clase es una tabla, cada atributo es un campo de la tabla
class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    done = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title


