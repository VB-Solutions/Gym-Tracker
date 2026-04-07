from django.shortcuts import render
from . import models
from rest_framework import viewsets
from .serializer import TaskSerializer  
# Create your views here.

class TaskViewSet(viewsets.ModelViewSet):
    # Especificamos qué serializador usará esta vista para traducir entre JSON y objetos Python.
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        """
        Sobreescribimos get_queryset para personalizar la consulta a la base de datos.
        Regla estricta de Django REST Framework: este método DEBE retornar un QuerySet.
        """
        # Obtenemos todas las tareas de la base de datos y las ordenamos por ID.
        tareas_filtradas = models.Task.objects.all().order_by('id')
        #tareas_filtradas = tareas_filtradas[:1]  # Limitamos el resultado al primer elemento usando slicing.
        # Al usar slicing ([:1]), obtenemos un QuerySet con un solo elemento,
        
        # Limitamos el resultado al primer elemento usando "slicing" ([:1]).
        # A nivel base de datos, esto ejecuta una consulta con "LIMIT 1".
        # Utilizamos [:1] en lugar de .first() porque el slicing preserva el tipo de dato
        # como un QuerySet (una "caja" con 1 elemento), evitando que la vista falle.
        #tareas_filtradas = tareas_filtradas[:1]
        
        return tareas_filtradas