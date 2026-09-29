from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import CustomExercise, Gym, Muscle, Routine


class GymTrackerAPITestCase(APITestCase):
    """Datos base: un gym con dos staff y un socio, más un gym ajeno."""

    def setUp(self):
        self.gym = Gym.objects.create(name='Gym Centro')
        self.other_gym = Gym.objects.create(name='Gym Ajeno')
        self.muscle = Muscle.objects.create(muscle_name='Pecho', zone='Tren superior')

        self.staff = self._create_user('staff@test.com', User.Role.STAFF, self.gym)
        self.other_staff = self._create_user('otro-staff@test.com', User.Role.STAFF, self.gym)
        self.person = self._create_user('socio@test.com', User.Role.PERSON, self.gym)

    def _create_user(self, email, role, *gyms):
        user = User.objects.create_user(email=email, password='pass1234', role=role)
        user.gyms.set(gyms)
        return user


class CustomExerciseTests(GymTrackerAPITestCase):
    def _payload(self):
        return {
            'name': 'Press con banda',
            'description': 'Press de pecho con banda elástica',
            'muscle': self.muscle.id,
            'gym': self.gym.id,
        }

    def test_staff_can_create_custom_exercise_with_description(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(reverse('custom-exercise-list'), self._payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exercise = CustomExercise.objects.get(id=response.data['id'])
        self.assertEqual(exercise.description, 'Press de pecho con banda elástica')

    def test_person_cannot_create_custom_exercise(self):
        self.client.force_authenticate(self.person)

        response = self.client.post(reverse('custom-exercise-list'), self._payload())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RoutineTests(GymTrackerAPITestCase):
    def setUp(self):
        super().setUp()
        self.routine = Routine.objects.create(
            name='Rutina inicial', gym=self.gym, staff=self.staff, person=self.person
        )

    def test_staff_creates_routine_as_its_staff(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(reverse('routine-list'), {
            'name': 'Fuerza',
            'gym': self.gym.id,
            'person': self.person.id,
            'staff': self.other_staff.id,  # Se ignora: el staff es quien crea
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Routine.objects.get(id=response.data['id']).staff, self.staff)

    def test_person_can_rename_own_routine_but_not_change_staff(self):
        self.client.force_authenticate(self.person)

        response = self.client.patch(
            reverse('routine-detail', args=[self.routine.id]),
            {'name': 'Rutina renombrada', 'staff': self.other_staff.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.routine.refresh_from_db()
        self.assertEqual(self.routine.name, 'Rutina renombrada')
        self.assertEqual(self.routine.staff, self.staff)

    def test_person_cannot_delete_routine(self):
        self.client.force_authenticate(self.person)

        response = self.client.delete(reverse('routine-detail', args=[self.routine.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Routine.objects.filter(id=self.routine.id).exists())

    def test_staff_can_delete_own_routine(self):
        self.client.force_authenticate(self.staff)

        response = self.client.delete(reverse('routine-detail', args=[self.routine.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GymQueryParamTests(GymTrackerAPITestCase):
    URL_NAMES = [
        'exercise-list',
        'custom-exercise-list',
        'gym-standard-exercise-video-list',
        'routine-list',
        'get_all_routines',
    ]

    def test_non_numeric_gym_returns_400(self):
        self.client.force_authenticate(self.staff)

        for url_name in self.URL_NAMES:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name), {'gym': 'abc'})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_gym_the_user_does_not_belong_to_returns_403(self):
        self.client.force_authenticate(self.staff)

        for url_name in self.URL_NAMES:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name), {'gym': self.other_gym.id})
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SchemaTests(APITestCase):
    def test_openapi_schema_is_generated(self):
        response = self.client.get(reverse('schema'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
