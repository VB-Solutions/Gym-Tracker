from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from .permissions import IsGymStaffOrAdminOrReadOnly
from .utils import get_gym_id_param, get_int_param, require_gym_role
from django.db.models import Prefetch, ProtectedError, Q

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
from .serializer import (
    CustomExerciseSerializer,
    ExerciseBlockSerializer,
    ExerciseSerializer,
    GymSerializer,
    GymStandardExerciseVideoSerializer,
    MuscleSerializer,
    RoutineSerializer,
    RoutineDetailSerializer,
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
        # Swagger genera el schema con un usuario anónimo
        if getattr(self, 'swagger_fake_view', False):
            return Gym.objects.none()

        return self.request.user.gyms.order_by('name')


class MuscleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para Músculos (Solo lectura).
    - GET /muscles/ -> Trae todos los músculos de la base de datos.
    - GET /muscles/<id>/ -> Trae un músculo específico.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MuscleSerializer


    queryset = Muscle.objects.order_by('muscle_name')


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

        # Valida que ?gym sea numérico y que el usuario pertenezca a ese gym
        gym_id = get_gym_id_param(self.request)

        #No se manda gym
        if not gym_id:
            return Exercise.objects.filter(customexercise__isnull=True).order_by('name')

        #Los standar y los custom del gym
        return Exercise.objects.filter(
            Q(customexercise__isnull=True) | Q(customexercise__gym_id=gym_id)
        ).distinct().order_by('name')



class CustomExerciseViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Ejercicios Personalizados (Custom Exercises).
    - GET /custom-exercises/?gym=<id> -> Trae todos los ejercicios custom de ese Gym (El parámetro ?gym es OBLIGATORIO al listar).
    - GET /custom-exercises/<id>/ -> Trae el detalle de un ejercicio custom específico.
    - POST /custom-exercises/ -> Crea un nuevo ejercicio custom (Solo STAFF o ADMIN de ese gym).
    - PUT/PATCH /custom-exercises/<id>/ -> Modifica un ejercicio custom (Solo STAFF o ADMIN de ese gym).
    - DELETE /custom-exercises/<id>/ -> Elimina un ejercicio custom (Solo STAFF o ADMIN de ese gym).
    """
    serializer_class = CustomExerciseSerializer
    # Editar y borrar: STAFF o ADMIN del gym del ejercicio (permiso a nivel objeto)
    permission_classes = [IsAuthenticated, IsGymStaffOrAdminOrReadOnly]

    def get_queryset(self):
        """
        Controla qué registros de la base de datos están disponibles.
        """
        if getattr(self, 'swagger_fake_view', False):
            return CustomExercise.objects.none()

        if self.action == 'list':
            gym_id = get_gym_id_param(self.request, required=True)
            return CustomExercise.objects.filter(gym_id=gym_id).order_by('name')


        return CustomExercise.objects.filter(gym__in=self.request.user.gyms.all())

    def perform_create(self, serializer):
        require_gym_role(
            self.request.user,
            serializer.validated_data.get('gym'),
            [Role.STAFF, Role.ADMIN],
            "Solo STAFF o ADMIN de este gimnasio pueden crear ejercicios.",
        )
        serializer.save()

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "No se puede borrar: el ejercicio está en rutinas. Primero sacalo de esas rutinas."
            )



class GymStandardExerciseVideoViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Videos Propios de Ejercicios Estándar.
    - GET /gym-standard-exercise-videos/?gym=<id> -> Trae los videos del gym (Obligatorio enviar el gym).
    - GET /gym-standard-exercise-videos/<id>/ -> Trae el detalle de un video específico.
    - POST /gym-standard-exercise-videos/ -> Asigna un video a un ejercicio estándar (Solo STAFF o ADMIN de ese gym).
    - PUT/PATCH /gym-standard-exercise-videos/<id>/ -> Edita el link del video (Solo STAFF o ADMIN de ese gym).
    - DELETE /gym-standard-exercise-videos/<id>/ -> Elimina el video (Solo STAFF o ADMIN de ese gym).
    """
    serializer_class = GymStandardExerciseVideoSerializer
    permission_classes = [IsAuthenticated, IsGymStaffOrAdminOrReadOnly]

    def get_queryset(self):
        """
        Controla qué registros de la base de datos están disponibles.
        """
        if getattr(self, 'swagger_fake_view', False):
            return GymStandardExerciseVideo.objects.none()

        if self.action == 'list':
            gym_id = get_gym_id_param(self.request, required=True)
            # Retorna solo los videos de ese gimnasio
            return GymStandardExerciseVideo.objects.filter(gym_id=gym_id).order_by('id')

        # Para retrieve, update o destroy, busca en los gimnasios del usuario
        return GymStandardExerciseVideo.objects.filter(gym__in=self.request.user.gyms.all())

    def perform_create(self, serializer):
        require_gym_role(
            self.request.user,
            serializer.validated_data.get('gym'),
            [Role.STAFF, Role.ADMIN],
            "Solo STAFF o ADMIN de este gimnasio pueden cargar videos.",
        )
        serializer.save()




class RoutineViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Gestión de Rutinas. Lo que ve cada uno depende de su rol en cada gimnasio
    (PERSON: las suyas | STAFF: las que armó | ADMIN: todas las del gym).

    ACCESIBLE POR TODOS (SOCIOS, STAFF, ADMIN):
    - GET /routines/ -> Trae las rutinas que podés ver. Con ?gym=<id> filtra por ese gimnasio.
    - GET /routines/<id>/ -> Trae el detalle completo de una rutina específica.
    - PUT/PATCH /routines/<id>/ -> Edita una rutina existente (solo el nombre).

    SOLO ACCESIBLE POR STAFF O ADMIN DEL GYM:
    - POST /routines/ -> Crea una nueva rutina. El staff es quien la crea; un ADMIN puede
                         asignársela a otro entrenador mandando `staff`.

    - DELETE /routines/<id>/ -> Elimina una rutina.
    """
    permission_classes = [IsAuthenticated]

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

    def get_queryset(self):
        """
        Filtra las rutinas según el rol del usuario en cada gimnasio.
        """
        if getattr(self, 'swagger_fake_view', False):
            return Routine.objects.none()

        qs = Routine.objects.visible_to(self.request.user)

        if self.action in ['list', 'retrieve']:
            # Todo lo que usa RoutineDetailSerializer, en un número fijo de queries (sin N+1)
            blocks = ExerciseBlock.objects.select_related(
                'exercise__muscle', 'exercise__customexercise',
            ).prefetch_related('exercise__gym_videos')
            qs = qs.select_related('gym', 'staff', 'person').prefetch_related(
                Prefetch('blocks', queryset=blocks),
            )

        if self.action == 'list':
            gym_id = get_gym_id_param(self.request)
            if gym_id:
                qs = qs.filter(gym_id=gym_id)

        return qs.order_by('id')

    def perform_create(self, serializer):
        """
        Validaciones antes de guardar una rutina nueva.
        """
        user = self.request.user
        gym = serializer.validated_data.get('gym')

        require_gym_role(
            user, gym, [Role.STAFF, Role.ADMIN],
            "Solo STAFF o ADMIN de este gimnasio pueden crear rutinas.",
        )

        # Por defecto el staff es quien crea la rutina (sale del token, no del JSON)
        staff = serializer.validated_data.get('staff') or user
        if staff != user and not user.has_gym_role(gym, Role.ADMIN):
            raise PermissionDenied("Solo un ADMIN del gimnasio puede asignarle la rutina a otro entrenador.")

        serializer.save(staff=staff)

    def perform_destroy(self, instance):
        require_gym_role(
            self.request.user, instance.gym_id, [Role.STAFF, Role.ADMIN],
            "Solo STAFF o ADMIN de este gimnasio pueden borrar rutinas.",
        )
        instance.delete()



class ExerciseBlockViewSet(viewsets.ModelViewSet):
    """
    Ejercicios de una rutina, cada uno con su día, orden y series.
    - GET /exercise-blocks/?routine=<id> -> Los bloques de esa rutina, por día y orden (?routine es OBLIGATORIO al listar).
    - GET /exercise-blocks/<id>/ -> Detalle de un bloque.
    - POST /exercise-blocks/ {routine, exercise, day_number, order, series_data} -> Solo STAFF o ADMIN del gym de la rutina.
    - PUT/PATCH /exercise-blocks/<id>/ -> Edita ejercicio, día, orden o series (Solo STAFF o ADMIN del gym).
    - DELETE /exercise-blocks/<id>/ -> Elimina el bloque (Solo STAFF o ADMIN del gym).
    Solo se ven y se editan bloques de rutinas que el usuario puede ver.
    """
    serializer_class = ExerciseBlockSerializer
    # Editar y borrar: STAFF o ADMIN del gym de la rutina (ExerciseBlock.gym_id)
    permission_classes = [IsAuthenticated, IsGymStaffOrAdminOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ExerciseBlock.objects.none()

        qs = ExerciseBlock.objects.filter(
            routine__in=Routine.objects.visible_to(self.request.user),
        ).select_related('routine', 'exercise')

        if self.action == 'list':
            qs = qs.filter(routine_id=get_int_param(self.request, 'routine', required=True))

        return qs

    def perform_create(self, serializer):
        require_gym_role(
            self.request.user,
            serializer.validated_data['routine'].gym_id,
            [Role.STAFF, Role.ADMIN],
            "Solo STAFF o ADMIN de este gimnasio pueden armar rutinas.",
        )
        serializer.save()
