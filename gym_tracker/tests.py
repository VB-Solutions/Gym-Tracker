from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import GymMembership, Role, User

from .models import (
    CustomExercise,
    Exercise,
    ExerciseBlock,
    Gym,
    GymStandardExerciseVideo,
    Muscle,
    Routine,
)


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
                self.assertEqual({routine['name'] for routine in response.data['results']}, names)

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


class ExerciseBlockTests(GymTrackerAPITestCase):
    def setUp(self):
        super().setUp()
        self.routine = Routine.objects.create(
            name='Fuerza', gym=self.gym, staff=self.staff, person=self.person
        )
        self.exercise = Exercise.objects.create(name='Sentadilla', description='Con barra')

    def _payload(self, **extra):
        return {
            'routine': self.routine.id,
            'exercise': self.exercise.id,
            'day_number': 1,
            'order': 1,
            'series_data': [{'repe': 12, 'peso': 50}, {'repe': 10}],
            **extra,
        }

    def _create(self, **extra):
        return self.client.post(reverse('exercise-block-list'), self._payload(**extra), format='json')

    def test_staff_adds_block_and_it_shows_in_the_routine(self):
        self.client.force_authenticate(self.staff)

        response = self._create()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['exercise_name'], 'Sentadilla')

        self.client.force_authenticate(self.person)
        routine = self.client.get(reverse('routine-detail', args=[self.routine.id]))
        self.assertEqual(routine.data['blocks'][0]['series_data'], [{'repe': 12, 'peso': 50}, {'repe': 10}])

    def test_person_can_read_but_not_write_blocks(self):
        block = ExerciseBlock.objects.create(routine=self.routine, exercise=self.exercise, day_number=1, order=1)
        self.client.force_authenticate(self.person)

        listing = self.client.get(reverse('exercise-block-list'), {'routine': self.routine.id})
        self.assertEqual([item['id'] for item in listing.data['results']], [block.id])

        self.assertEqual(self._create(order=2).status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(reverse('exercise-block-detail', args=[block.id]), {'order': 5})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_add_blocks_to_a_routine_you_cannot_see(self):
        # other_staff es STAFF del gym pero la rutina es de staff
        self.client.force_authenticate(self.other_staff)

        response = self._create()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('routine', response.data)

    def test_custom_exercise_must_belong_to_the_routine_gym(self):
        foreign = CustomExercise.objects.create(name='Ajeno', description='x', gym=self.other_gym)
        self.client.force_authenticate(self.staff)

        response = self._create(exercise=foreign.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exercise', response.data)

    def test_day_and_order_are_unique_per_routine(self):
        self.client.force_authenticate(self.staff)
        self._create()

        response = self._create()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_series_data_returns_400(self):
        self.client.force_authenticate(self.staff)

        for series_data in ['12x50', [{'repe': 0}], [{'repe': 10, 'peso': -5}], [{'reps': 10}], [{'repe': True}]]:
            with self.subTest(series_data=series_data):
                response = self._create(series_data=series_data)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('series_data', response.data)

    def test_day_and_order_start_at_one(self):
        self.client.force_authenticate(self.staff)

        self.assertEqual(self._create(day_number=0).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._create(order=0).status_code, status.HTTP_400_BAD_REQUEST)

    def test_listing_requires_routine_param(self):
        self.client.force_authenticate(self.staff)

        self.assertEqual(self.client.get(reverse('exercise-block-list')).status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(reverse('exercise-block-list'), {'routine': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RoutineDetailTests(GymTrackerAPITestCase):
    """Lo que devuelve GET /routines/: videos por gym y cantidad de queries."""

    def setUp(self):
        super().setUp()
        self.standard = Exercise.objects.create(name='Sentadilla', description='Con barra', muscle=self.muscle)
        self.custom = CustomExercise.objects.create(
            name='Press con banda', description='x', gym=self.gym, video='https://videos.test/banda',
        )
        GymStandardExerciseVideo.objects.create(gym=self.gym, exercise=self.standard, video='https://videos.test/centro')
        GymStandardExerciseVideo.objects.create(gym=self.other_gym, exercise=self.standard, video='https://videos.test/ajeno')

    def _routine_with_blocks(self, name):
        routine = Routine.objects.create(name=name, gym=self.gym, staff=self.staff, person=self.person)
        ExerciseBlock.objects.create(routine=routine, exercise=self.standard, day_number=1, order=1)
        ExerciseBlock.objects.create(routine=routine, exercise=self.custom, day_number=1, order=2)
        return routine

    def _list_routines(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse('routine-list'))
        return response, len(queries)

    def test_video_url_uses_the_routine_gym(self):
        routine = self._routine_with_blocks('Piernas')
        self.client.force_authenticate(self.person)

        response = self.client.get(reverse('routine-detail', args=[routine.id]))

        videos = [block['exercise']['video_url'] for block in response.data['blocks']]
        self.assertEqual(videos, ['https://videos.test/centro', 'https://videos.test/banda'])

    def test_number_of_queries_does_not_grow_with_routines(self):
        self.client.force_authenticate(self.person)
        self._routine_with_blocks('Rutina 1')
        response, queries_with_one = self._list_routines()
        self.assertEqual(response.data['count'], 1)

        for number in range(2, 6):
            self._routine_with_blocks(f'Rutina {number}')
        response, queries_with_five = self._list_routines()

        self.assertEqual(response.data['count'], 5)
        self.assertEqual(queries_with_five, queries_with_one)

    def test_lists_are_paginated(self):
        for number in range(1, 4):
            Routine.objects.create(name=f'Rutina {number}', gym=self.gym, staff=self.staff, person=self.person)
        self.client.force_authenticate(self.person)

        response = self.client.get(reverse('routine-list'), {'page_size': 2})

        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])


class GymStandardExerciseVideoTests(GymTrackerAPITestCase):
    def setUp(self):
        super().setUp()
        self.standard = Exercise.objects.create(name='Sentadilla', description='Con barra')
        self.client.force_authenticate(self.staff)

    def _create(self, exercise):
        return self.client.post(reverse('gym-standard-exercise-video-list'), {
            'gym': self.gym.id, 'exercise': exercise.id, 'video': 'https://videos.test/x',
        })

    def test_staff_adds_video_to_standard_exercise(self):
        self.assertEqual(self._create(self.standard).status_code, status.HTTP_201_CREATED)

    def test_custom_exercises_cannot_get_a_standard_video(self):
        custom = CustomExercise.objects.create(name='Propio', description='x', gym=self.gym)

        response = self._create(custom)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exercise', response.data)

    def test_one_video_per_exercise_and_gym(self):
        self._create(self.standard)

        self.assertEqual(self._create(self.standard).status_code, status.HTTP_400_BAD_REQUEST)


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
