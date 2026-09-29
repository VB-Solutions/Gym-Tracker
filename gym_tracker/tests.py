from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import GymMembership, Role, User

from .models import CustomExercise, Gym, Muscle, Routine


class GymTrackerAPITestCase(APITestCase):
    """Datos base: un gym con un admin, dos staff y un socio, más un gym ajeno."""

    def setUp(self):
        self.gym = Gym.objects.create(name='Gym Centro')
        self.other_gym = Gym.objects.create(name='Gym Ajeno')
        self.muscle = Muscle.objects.create(muscle_name='Pecho', zone='Tren superior')

        self.admin = self._create_user('admin@test.com', Role.ADMIN, self.gym)
        self.staff = self._create_user('staff@test.com', Role.STAFF, self.gym)
        self.other_staff = self._create_user('otro-staff@test.com', Role.STAFF, self.gym)
        self.person = self._create_user('socio@test.com', Role.PERSON, self.gym)

    def _create_user(self, email, role, *gyms):
        user = User.objects.create_user(email=email, password='pass1234')
        for gym in gyms:
            GymMembership.objects.create(user=user, gym=gym, role=role)
        return user


class CustomExerciseTests(GymTrackerAPITestCase):
    def _payload(self, gym):
        return {
            'name': 'Press con banda',
            'description': 'Press de pecho con banda elástica',
            'muscle': self.muscle.id,
            'gym': gym.id,
        }

    def test_staff_can_create_custom_exercise_with_description(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(reverse('custom-exercise-list'), self._payload(self.gym))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exercise = CustomExercise.objects.get(id=response.data['id'])
        self.assertEqual(exercise.description, 'Press de pecho con banda elástica')

    def test_person_cannot_create_custom_exercise(self):
        self.client.force_authenticate(self.person)

        response = self.client.post(reverse('custom-exercise-list'), self._payload(self.gym))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_is_per_gym(self):
        # Es STAFF en un gym y socio en otro: solo puede crear ejercicios donde es STAFF
        GymMembership.objects.create(user=self.staff, gym=self.other_gym, role=Role.PERSON)
        self.client.force_authenticate(self.staff)

        response = self.client.post(reverse('custom-exercise-list'), self._payload(self.other_gym))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_person_cannot_edit_custom_exercise(self):
        exercise = CustomExercise.objects.create(name='Remo', description='Remo', gym=self.gym)
        self.client.force_authenticate(self.person)

        response = self.client.patch(
            reverse('custom-exercise-detail', args=[exercise.id]), {'name': 'Otro'}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RoutineTests(GymTrackerAPITestCase):
    def setUp(self):
        super().setUp()
        self.routine = Routine.objects.create(
            name='Rutina inicial', gym=self.gym, staff=self.staff, person=self.person
        )

    def _create_routine(self, **extra):
        return self.client.post(reverse('routine-list'), {
            'name': 'Fuerza',
            'gym': self.gym.id,
            'person': self.person.id,
            **extra,
        })

    def test_staff_creates_routine_as_its_staff(self):
        self.client.force_authenticate(self.staff)

        response = self._create_routine()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Routine.objects.get(id=response.data['id']).staff, self.staff)

    def test_staff_cannot_assign_routine_to_other_staff(self):
        self.client.force_authenticate(self.staff)

        response = self._create_routine(staff=self.other_staff.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_assign_routine_to_staff(self):
        self.client.force_authenticate(self.admin)

        response = self._create_routine(staff=self.other_staff.id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Routine.objects.get(id=response.data['id']).staff, self.other_staff)

    def test_routine_person_must_be_person_of_the_gym(self):
        self.client.force_authenticate(self.staff)

        response = self._create_routine(person=self.other_staff.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('person', response.data)

    def test_person_cannot_create_routine(self):
        self.client.force_authenticate(self.person)

        response = self._create_routine()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_list_shows_routines_by_role(self):
        Routine.objects.create(name='De otro staff', gym=self.gym, staff=self.other_staff, person=self.person)

        expected = {
            self.person: {'Rutina inicial', 'De otro staff'},
            self.staff: {'Rutina inicial'},
            self.admin: {'Rutina inicial', 'De otro staff'},
        }
        for user, names in expected.items():
            with self.subTest(user=user.email):
                self.client.force_authenticate(user)
                response = self.client.get(reverse('routine-list'), {'gym': self.gym.id})
                self.assertEqual({routine['name'] for routine in response.data}, names)

    def test_person_loses_access_after_leaving_the_gym(self):
        GymMembership.objects.filter(user=self.person, gym=self.gym).delete()
        self.client.force_authenticate(self.person)

        response = self.client.get(reverse('routine-detail', args=[self.routine.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_rename_routine_after_person_left(self):
        GymMembership.objects.filter(user=self.person, gym=self.gym).delete()
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            reverse('routine-detail', args=[self.routine.id]), {'name': 'Archivada'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GymQueryParamTests(GymTrackerAPITestCase):
    URL_NAMES = [
        'exercise-list',
        'custom-exercise-list',
        'gym-standard-exercise-video-list',
        'routine-list',
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
