from rest_framework import serializers

from .models import (
    CustomExercise,
    Exercise,
    ExerciseBlock,
    Gym,
    GymStandardExerciseVideo,
    Muscle,
    Routine,
)

"""
    Serializers planos
    son para los Modelos basicos
"""

class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ('id', 'name')


class MuscleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscle
        fields = ('id', 'muscle_name', 'zone')


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ('id', 'name', 'muscle','description')


class CustomExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomExercise
        fields = ('id', 'name', 'muscle', 'gym', 'video')
        
    def validate_gym(self, value):
        if self.instance and self.instance.gym != value:
            raise serializers.ValidationError("No se permite cambiar el gimnasio de un ejercicio existente.")
        return value

    def __init__(self, *args, **kwargs):
        # Primero ejecutamos el constructor original
        super(CustomExerciseSerializer, self).__init__(*args, **kwargs)
        
        # 'self.instance' existe solo cuando estamos haciendo un UPDATE (PUT/PATCH)
        # Si 'self.instance' es None, significa que es un CREATE (POST)
        if self.instance is not None:
            self.fields['gym'].read_only = True


class GymStandardExerciseVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymStandardExerciseVideo
        fields = ('id', 'gym', 'exercise', 'video')
        
        
    def validate_exercise(self, value):
        if self.instance and self.instance.exercise != value:
            raise serializers.ValidationError("No se permite cambiar el exercise video.")
        return value
    
    def validate_gym(self, value):
        if self.instance and self.instance.gym != value:
            raise serializers.ValidationError("No se permite cambiar el gimnasio de un video.")
        return value
    
    

    def __init__(self, *args, **kwargs):
        # Primero ejecutamos el constructor original
        super(GymStandardExerciseVideoSerializer, self).__init__(*args, **kwargs)
        
        # 'self.instance' existe solo cuando estamos haciendo un UPDATE (PUT/PATCH)
        # Si 'self.instance' es None, significa que es un CREATE (POST)
        if self.instance is not None:
            self.fields['gym'].read_only = True
            self.fields['exercise'].read_only = True


class RoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routine
        fields = ('id', 'name', 'gym', 'staff', 'person')
        
        
    def __init__(self, *args, **kwargs):
        # Primero ejecutamos el constructor original
        super(RoutineSerializer, self).__init__(*args, **kwargs)
        
        # 'self.instance' existe solo cuando estamos haciendo un UPDATE (PUT/PATCH)
        # Si 'self.instance' es None, significa que es un CREATE (POST)
        if self.instance is not None:
            self.fields['gym'].read_only = True
            self.fields['person'].read_only = True

    def validate(self, attrs):
        gym = attrs.get('gym') or getattr(self.instance, 'gym', None)
        person = attrs.get('person') or getattr(self.instance, 'person', None)

        if gym and person and not person.gyms.filter(id=gym.id).exists():
            raise serializers.ValidationError(
                {"person": "La persona asignada debe pertenecer al gimnasio de la rutina."}
            )

        return attrs



        
class ExerciseInBlockSerializer(serializers.ModelSerializer):
    """
    Este serializer extrae la información del ejercicio 
    para mostrarla dentro de un bloque. Resuelve dinámicamente 
    qué video mostrar dependiendo si es Custom o Standard.
    """
    # Traemos el nombre del músculo usando la relación (source)
    muscle_name = serializers.CharField(source='muscle.muscle_name', read_only=True)
    # Declaramos un campo que vamos a calcular nosotros mismos
    video_url = serializers.SerializerMethodField()
    
    '''
    source='muscle.muscle_name': Por defecto, si pusiéramos solo muscle, DRF enviaría el número 
    de ID (ej. 3). Al usar source, le decimos a Django que "viaje" hasta la tabla de músculos y
    nos traiga el texto del nombre. read_only=True significa que este campo es solo para lectura, 
    no para guardar.

serializers.SerializerMethodField(): Esto es poderoso. Le dice a DRF: "Este campo (video_url) no
existe en la base de datos de esta forma. Lo voy a calcular yo mismo usando una función". 
DRF buscará automáticamente una función llamada get_video_url para llenar este dato.
(La función get_video_url que vimos antes hace exactamente eso: decide qué video mostrar).
    '''

    class Meta:
        model = Exercise
        fields = ('id', 'name', 'muscle_name', 'video_url')

    def get_video_url(self, obj):
        # 1. Obtenemos el gimnasio desde el contexto (se lo pasaremos desde la View)
        gym = self.context.get('gym')
        if not gym:
            return None

        # 2. Si el ejercicio es Custom (Django lo sabe mágicamente por la herencia)
        if hasattr(obj, 'customexercise'):
            return obj.customexercise.video

        # 3. Si es Estándar, buscamos si este gym en particular le puso un video
        video_gym = GymStandardExerciseVideo.objects.filter(
            gym=gym, 
            exercise=obj
        ).first()
        
        return video_gym.video if video_gym else None


class ExerciseBlockDetailSerializer(serializers.ModelSerializer):
    """
    Detalle del bloque. En lugar de devolver solo el ID del ejercicio,
    anida toda la información que definimos en ExerciseInBlockSerializer.
    """
    # Anidamos el ejercicio
    exercise = ExerciseInBlockSerializer(read_only=True)

    class Meta:
        model = ExerciseBlock
        fields = ('id', 'day_number', 'order', 'series_data', 'exercise')


class RoutineDetailSerializer(serializers.ModelSerializer):
    """
    El 'Gran Serializer'. Trae la Rutina, los nombres legibles 
    de las relaciones y TODOS sus bloques de ejercicios ordenados.
    """
    # Usamos related_name='blocks' (el que pusiste en models.py) para traer la lista de bloques
    blocks = ExerciseBlockDetailSerializer(many=True, read_only=True)
    '''
    blocks = ...: Funciona igual que la anidación anterior, pero con many=True. Esto le avisa a DRF que no hay un solo bloque,
    sino una lista de ellos. Él se encarga de armar el array (los corchetes [] en JSON) y meter todos los bloques usando el traductor
    ExerciseBlockDetailSerializer
    '''
    # En lugar de mandar solo el ID, mandamos el nombre del Gym
    gym_name = serializers.CharField(source='gym.name', read_only=True)
    
    # Hacemos lo mismo para staff y person (asumiendo que usan email por tu app Users)
    staff_email = serializers.EmailField(source='staff.email', read_only=True)
    person_email = serializers.EmailField(source='person.email', read_only=True)

    class Meta:
        model = Routine
        # Mandamos los IDs originales por si el Frontend los necesita para algo,
        # más los nombres legibles, y finalmente el arreglo de bloques.
        fields = (
            'id', 'name', 
            'gym', 'gym_name', 
            'staff', 'staff_email', 
            'person', 'person_email', 
            'blocks'
        )
