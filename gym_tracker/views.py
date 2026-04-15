from requests import request
from rest_framework import viewsets , permissions , generics
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from .permissions import IsStaffRole, IsAdminRole , IsPersonRole
from django.db.models import Q

from .models import (
    CustomExercise,
    Exercise,
    ExerciseBlock,
    Gym,
    GymStandardExerciseVideo,
    Muscle,
    Routine,
)
from .serializer import (
    CustomExerciseSerializer,
    #ExerciseBlockSerializer,
    ExerciseSerializer,
    GymSerializer,
    GymStandardExerciseVideoSerializer,
    MuscleSerializer,
    RoutineSerializer,
    RoutineDetailSerializer,
    ExerciseBlockDetailSerializer,
    ExerciseInBlockSerializer
)




class GymViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para Gimnasios (Solo lectura).
    - GET /gyms/ -> Trae todos los gimnasios a los que pertenece el usuario.
    - GET /gyms/<id>/ -> Trae el detalle de un gimnasio específico.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GymSerializer
    
    def get_queryset(self):
        
        return self.request.user.gyms.all()


class MuscleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para Músculos (Solo lectura).
    - GET /muscles/ -> Trae todos los músculos de la base de datos.
    - GET /muscles/<id>/ -> Trae un músculo específico.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MuscleSerializer
    

    queryset = Muscle.objects.all()


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para Ejercicios Estándar (Solo lectura).
    - GET /exercises/ -> Trae todos los ejercicios estándar.
    - GET /exercises/<id>/ -> Trae un ejercicio específico.
    - GET /exercises/?gym=<id> -> Trae los Estándar + los Custom de ese Gym.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSerializer
    
    def get_queryset(self):

        gym_id = self.request.query_params.get('gym')
        
        #No se manda gym
        if not gym_id:
            return Exercise.objects.filter(customexercise__isnull=True)
            
       # Se manda un gym en el que no estoy
        if not self.request.user.gyms.filter(id=gym_id).exists():
            raise PermissionDenied("No tienes acceso a los ejercicios de este gimnasio.")

        #Los standar y los custom del gym
        return Exercise.objects.filter(
            Q(customexercise__isnull=True) | Q(customexercise__gym_id=gym_id)
        ).distinct()



class CustomExerciseViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Ejercicios Personalizados (Custom Exercises).
    - GET /custom-exercises/?gym=<id> -> Trae todos los ejercicios custom de ese Gym (El parámetro ?gym es OBLIGATORIO al listar).
    - GET /custom-exercises/<id>/ -> Trae el detalle de un ejercicio custom específico.
    - POST /custom-exercises/ -> Crea un nuevo ejercicio custom (Solo STAFF o ADMIN).
    - PUT/PATCH /custom-exercises/<id>/ -> Modifica un ejercicio custom (Solo STAFF o ADMIN).
    - DELETE /custom-exercises/<id>/ -> Elimina un ejercicio custom (Solo STAFF o ADMIN).
    """
    serializer_class = CustomExerciseSerializer
    
    def get_permissions(self):
        # Si intentan actualizar, borrar o crear, exigimos que sean STAFF o ADMIN
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            return [IsAuthenticated(), IsStaffRole() | IsAdminRole()]
        
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Controla qué registros de la base de datos están disponibles.
        """
        if self.action == 'list':
            gym_id = self.request.query_params.get('gym')
            
            if not gym_id:
                raise ValidationError({"gym": "Debes pasar un id de gimnasio en la URL (?gym=X)."})
                
            if not self.request.user.gyms.filter(id=gym_id).exists():
                raise PermissionDenied("Debes pasar un id de gimnasio al que pertenezcas.")
                
            return CustomExercise.objects.filter(gym_id=gym_id)


        return CustomExercise.objects.filter(gym__in=self.request.user.gyms.all())
    
    def perform_create(self, serializer):
        gym_solicitado = serializer.validated_data.get('gym')
        if gym_solicitado not in self.request.user.gyms.all():
            raise PermissionDenied("No puedes crear un ejercicio en un gimnasio al que no perteneces.")
        serializer.save()
        
    def perform_update(self, serializer):
        gym_solicitado = serializer.validated_data.get('gym')
        if gym_solicitado and gym_solicitado not in self.request.user.gyms.all():
            raise PermissionDenied("No puedes mover este ejercicio a un gimnasio al que no perteneces.")
        serializer.save()
    


class GymStandardExerciseVideoViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Videos Propios de Ejercicios Estándar.
    - GET /gym-standard-exercise-videos/?gym=<id> -> Trae los videos del gym (Obligatorio enviar el gym).
    - GET /gym-standard-exercise-videos/<id>/ -> Trae el detalle de un video específico.
    - POST /gym-standard-exercise-videos/ -> Asigna un video a un ejercicio estándar (Solo STAFF o ADMIN).
    - PUT/PATCH /gym-standard-exercise-videos/<id>/ -> Edita el link del video (Solo STAFF o ADMIN).
    - DELETE /gym-standard-exercise-videos/<id>/ -> Elimina el video (Solo STAFF o ADMIN).
    """
    serializer_class = GymStandardExerciseVideoSerializer
    
    def get_permissions(self):
        # Si intentan actualizar, borrar o crear, exigimos que sean STAFF o ADMIN
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            return [IsAuthenticated(), IsStaffRole() | IsAdminRole()]
        
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Controla qué registros de la base de datos están disponibles.
        """
        if self.action == 'list':
            gym_id = self.request.query_params.get('gym')
            
            
            if not gym_id:
                raise ValidationError({"gym": "Debes pasar un id de gimnasio en la URL (?gym=X)."})
            
            if not self.request.user.gyms.filter(id=gym_id).exists():
                raise PermissionDenied("Debes solicitar un id de gimnasio al que pertenezcas.")
                
            # Retorna solo los videos de ese gimnasio
            return GymStandardExerciseVideo.objects.filter(gym_id=gym_id)

        # Para retrieve, update o destroy, busca en los gimnasios del usuario
        return GymStandardExerciseVideo.objects.filter(gym__in=self.request.user.gyms.all())
    
    def perform_create(self, serializer):
        # Validamos inyección de ID de gimnasio al crear
        gym_solicitado = serializer.validated_data.get('gym')
        if gym_solicitado not in self.request.user.gyms.all():
            raise PermissionDenied("No puedes crear un video en un gimnasio al que no perteneces.")
        serializer.save()
   



class RoutineViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Gestión de Rutinas.
    
    ACCESIBLE POR TODOS (SOCIOS, STAFF, ADMIN):
    - GET /routines/?gym=<id> -> Trae la lista de rutinas filtradas por rol (Obligatorio enviar el gym).
                                 (PERSON: Ve las suyas | STAFF: Ve las que creó | ADMIN: Ve todas del gym).
    - GET /routines/<id>/ -> Trae el detalle completo de una rutina específica.
    - PUT/PATCH /routines/<id>/ -> Edita una rutina existente.
    
    SOLO ACCESIBLE POR STAFF O ADMIN:
    - POST /routines/ -> Crea una nueva rutina (El creador debe pertenecer al gym indicado).
    
    - DELETE /routines/<id>/ -> Elimina una rutina.
    """
    # Usamos el Detail para recuperar datos complejos (con bloques), 
    # pero podrías querer usar el plano (RoutineSerializer) para listar y crear.
    # Por ahora dejamos el Detail como pediste.
    def get_serializer_class(self):
        """
        Decide dinámicamente qué Serializer usar.
        """
        # GET
        # 
        if self.action in ['list', 'retrieve']:
            return RoutineDetailSerializer
            
        #  (POST, PUT, PATCH)
        return RoutineSerializer
    
    def get_permissions(self):
        # Si la acción es CREAR, solo STAFF o ADMIN
        if self.action == 'create':
            return [IsAuthenticated(), IsStaffRole() | IsAdminRole()]
            
        # Si la acción es EDITAR o BORRAR...
        if self.action in ['update', 'partial_update', 'destroy']:

            return [IsAuthenticated()] 
            
        # Para listar y ver detalle (GET)
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Filtra las rutinas según el rol del usuario y el gimnasio solicitado.
        """
        user = self.request.user
        role = user.role
        
        # Empezamos con una consulta vacía por seguridad
        qs = Routine.objects.none()

        # Comportamiento para listar (GET /routines/)
        if self.action == 'list':
            gym_id = self.request.query_params.get('gym')
            
            # 1. Validación: Obligar a mandar el gimnasio
            if not gym_id:
                raise ValidationError({"gym": "Debes pasar un id de gimnasio en la URL (?gym=X)."})
                
            # 2. Seguridad: ¿Pertenece a ese gimnasio?
            if not user.gyms.filter(id=gym_id).exists():
                raise PermissionDenied("No tienes acceso a las rutinas de este gimnasio.")

            # 3. Filtrar según el ROL sobre ese gimnasio específico
            if role == 'PERSON':
                qs = Routine.objects.filter(gym_id=gym_id, person=user)
            elif role == 'STAFF':
                qs = Routine.objects.filter(gym_id=gym_id, staff=user)
            elif role == 'ADMIN':
                qs = Routine.objects.filter(gym_id=gym_id) # El admin ve todas las del gym

            return qs

        # Comportamiento para detalle/editar/borrar (ej: GET /routines/5/)
        # Acá dejamos que Django busque entre todas las rutinas que el usuario tiene derecho a ver
        if role == 'PERSON':
            qs = Routine.objects.filter(person=user)
        elif role == 'STAFF':
            qs = Routine.objects.filter(staff=user)
        elif role == 'ADMIN':
            # El admin busca en todos los gimnasios que administra
            qs = Routine.objects.filter(gym__in=user.gyms.all())
            
        return qs

    def perform_create(self, serializer):
        """
        Validaciones antes de guardar una rutina nueva.
        """
        gym_solicitado = serializer.validated_data.get('gym')
        person_solicitada = serializer.validated_data.get('person')
        
        # Validar que el Staff/Admin pertenezca al gimnasio donde intenta crear la rutina
        if gym_solicitado not in self.request.user.gyms.all():
            raise PermissionDenied("No puedes crear una rutina en un gimnasio al que no perteneces.")

        # La persona objetivo también debe pertenecer al gimnasio de la rutina.
        if person_solicitada and not person_solicitada.gyms.filter(id=gym_solicitado.id).exists():
            raise ValidationError({"person": "La persona asignada no pertenece a este gimnasio."})
            
        # Opcional (pero recomendado): Asegurarte de que el campo 'staff' sea el usuario actual
        # Así el Staff no tiene que mandar su propio ID en el JSON, lo sacás del Token.
        serializer.save(staff=self.request.user)

    def perform_update(self, serializer):
        """
        Validaciones antes de actualizar una rutina.
        """
        person_solicitada = serializer.validated_data.get('person') or serializer.instance.person
        gym_actual = serializer.instance.gym
        gym_solicitado = serializer.validated_data.get('gym')
        
        # Evitar que muevan la rutina a un gimnasio ajeno
        if gym_solicitado and gym_solicitado not in self.request.user.gyms.all():
            raise PermissionDenied("No puedes mover esta rutina a un gimnasio al que no perteneces.")

        # La persona de la rutina debe pertenecer al gimnasio de la rutina.
        if person_solicitada and not person_solicitada.gyms.filter(id=gym_actual.id).exists():
            raise ValidationError({"person": "La persona asignada no pertenece al gimnasio de esta rutina."})
            
        serializer.save()




# class ExerciseBlockViewSet(viewsets.ModelViewSet):
#     queryset = ExerciseBlock.objects.all()
#     serializer_class = ExerciseBlockSerializer
  
    


class GetAllRoutinesView(generics.ListAPIView):
    """
     Aca le pedis que te traiga todas las rutinas.
     Se fija que rol tenes
     SI pasas el query Parameter gym (EL ID), filtra por ese gym
     
    """    
    serializer_class = RoutineSerializer 
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        
        user = self.request.user
        gym_id = self.request.query_params.get('gym')
        
        #si person
        if user.role == 'PERSON':
            qs = Routine.objects.filter(person=user)
            if gym_id :
                qs = qs.filter(gym_id=gym_id)
            return qs

        #Si staff
        elif user.role == 'STAFF':
            qs = Routine.objects.filter(staff=user)
            if gym_id :
                qs = qs.filter(gym_id=gym_id)
            return  qs

        #Si admin
        elif user.role == 'ADMIN':

            qs = Routine.objects.filter(gym__in=user.gyms.all())
            
            if gym_id:
               
                qs = qs.filter(gym_id=gym_id)
            return qs

        
        # devulve nada por las dudas
        return Routine.objects.none()
    
