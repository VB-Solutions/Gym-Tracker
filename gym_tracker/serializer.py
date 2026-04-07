from rest_framework import serializers
from .models import Task

#esto de aca es para transformar el objeto a un JSON 
#para pasarselo con un get a los homoFrontend y que lo puedan usar

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        #fields = ('id', 'title', 'description', 'done') asi para elejir
        fields = '__all__' #se pasan todos los campos del modelo Task
        
