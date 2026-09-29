from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from users.models import Role

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
        fields = ('id', 'name', 'description', 'muscle', 'gym', 'video')

    def __init__(self, *args, **kwargs):
        # Primero ejecutamos el constructor original
        super(CustomExerciseSerializer, self).__init__(*args, **kwargs)

        # 'self.instance' existe solo cuando estamos haciendo un UPDATE (PUT/PATCH)
        # Si 'self.instance' es None, significa que es un CREATE (POST)
        if self.instance is not None:
            self.fields['gym'].read_only = True

    def validate(self, attrs):
        # Nombre único dentro del gimnasio, sin importar mayúsculas
        gym = attrs.get('gym') or self.instance.gym
        name = attrs.get('name') or self.instance.name

        same_name = CustomExercise.objects.filter(gym=gym, name__iexact=name)
        if self.instance is not None:
            same_name = same_name.exclude(pk=self.instance.pk)
        if same_name.exists():
            raise serializers.ValidationError(
                {"name": "Ya existe un ejercicio propio con este nombre en el gimnasio."}
            )

        return attrs


class GymStandardExerciseVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymStandardExerciseVideo
        fields = ('id', 'gym', 'exercise', 'video')
        
        
    def validate_exercise(self, value):
        # Los ejercicios propios guardan su video en CustomExercise.video
        if CustomExercise.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError(
                "Solo se cargan videos de ejercicios estándar; los ejercicios propios tienen su propio campo `video`."
            )
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
        # Al editar solo se puede cambiar el nombre; el staff lo asigna la View al crear
        if self.instance is not None:
            self.fields['gym'].read_only = True
            self.fields['person'].read_only = True
            self.fields['staff'].read_only = True

    def validate(self, attrs):
        # Al editar gym, person y staff son de solo lectura: solo hay que validar al crear
        if self.instance is not None:
            return attrs

        gym = attrs['gym']
        person = attrs['person']
        staff = attrs.get('staff')

        if not person.has_gym_role(gym, Role.PERSON):
            raise serializers.ValidationError(
                {"person": "La persona asignada tiene que ser socio (PERSON) del gimnasio de la rutina."}
            )

        if staff and not staff.has_gym_role(gym, Role.STAFF, Role.ADMIN):
            raise serializers.ValidationError(
                {"staff": "El entrenador asignado tiene que ser STAFF o ADMIN del gimnasio de la rutina."}
            )

        return attrs



class ExerciseBlockSerializer(serializers.ModelSerializer):
    """
    Para crear/editar los ejercicios de una rutina.
    series_data: [{"repe": 12, "peso": 50}, ...] (ver validators.validate_series_data).
    """
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = ExerciseBlock
        fields = ('id', 'routine', 'exercise', 'exercise_name', 'day_number', 'order', 'series_data')
        extra_kwargs = {
            'day_number': {'min_value': 1},
            'order': {'min_value': 1},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo se pueden elegir rutinas que el usuario puede ver
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['routine'].queryset = Routine.objects.visible_to(request.user)

        # Un bloque no se puede mover a otra rutina
        if self.instance is not None:
            self.fields['routine'].read_only = True

    def validate(self, attrs):
        routine = attrs.get('routine') or self.instance.routine
        exercise = attrs.get('exercise') or self.instance.exercise

        # Estándar, o propio del mismo gimnasio de la rutina
        custom = CustomExercise.objects.filter(pk=exercise.pk).first()
        if custom and custom.gym_id != routine.gym_id:
            raise serializers.ValidationError(
                {"exercise": "El ejercicio propio tiene que ser del mismo gimnasio de la rutina."}
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

    def get_video_url(self, obj) -> str | None:
        # 1. Obtenemos el gimnasio de la rutina desde el contexto (lo pasa ExerciseBlockDetailSerializer)
        gym_id = self.context.get('gym_id')
        if not gym_id:
            return None

        # 2. Si el ejercicio es Custom (Django lo sabe mágicamente por la herencia)
        if hasattr(obj, 'customexercise'):
            return obj.customexercise.video

        # 3. Si es Estándar, buscamos si este gym en particular le puso un video.
        # Se filtra en Python para aprovechar el prefetch de la View (sin una query por bloque)
        return next(
            (gym_video.video for gym_video in obj.gym_videos.all() if gym_video.gym_id == gym_id),
            None,
        )


class ExerciseBlockDetailSerializer(serializers.ModelSerializer):
    """
    Detalle del bloque. En lugar de devolver solo el ID del ejercicio,
    anida toda la información que definimos en ExerciseInBlockSerializer.
    """
    # Anidamos el ejercicio (con el video que corresponde al gym de la rutina)
    exercise = serializers.SerializerMethodField()

    class Meta:
        model = ExerciseBlock
        fields = ('id', 'day_number', 'order', 'series_data', 'exercise')

    @extend_schema_field(ExerciseInBlockSerializer)
    def get_exercise(self, block):
        context = {**self.context, 'gym_id': block.routine.gym_id}
        return ExerciseInBlockSerializer(block.exercise, context=context).data


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
