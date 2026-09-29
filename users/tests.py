from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gym_tracker.models import Gym

from .models import GymMembership, Role, User


class GymScopedUserEndpointsTests(APITestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Gym Centro')
        self.other_gym = Gym.objects.create(name='Gym Ajeno')

        self.staff = self._create_user('staff@test.com', Role.STAFF, self.gym)
        self.person = self._create_user('socio@test.com', Role.PERSON, self.gym)
        self.foreign_staff = self._create_user('staff-ajeno@test.com', Role.STAFF, self.other_gym)
        self.foreign_person = self._create_user('socio-ajeno@test.com', Role.PERSON, self.other_gym)

    def _create_user(self, email, role, *gyms):
        user = User.objects.create_user(email=email, password='pass1234')
        for gym in gyms:
            GymMembership.objects.create(user=user, gym=gym, role=role)
        return user

    def _emails(self, response):
        return [user['email'] for user in response.data]

    def test_anonymous_cannot_list_users(self):
        for url_name in ['gym-admin-list', 'gym-staff-list', 'gym-person-list']:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertIn(
                    response.status_code,
                    (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
                )

    def test_person_cannot_list_people(self):
        self.client.force_authenticate(self.person)

        response = self.client.get(reverse('gym-person-list'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_person_only_sees_staff_from_own_gyms(self):
        self.client.force_authenticate(self.person)

        response = self.client.get(reverse('gym-staff-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._emails(response), ['staff@test.com'])

    def test_staff_only_sees_people_from_own_gyms(self):
        self.client.force_authenticate(self.staff)

        response = self.client.get(reverse('gym-person-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._emails(response), ['socio@test.com'])

    def test_people_list_only_covers_gyms_where_viewer_is_staff(self):
        # Es socio del gym ajeno: no por eso puede ver a los otros socios de ese gym
        GymMembership.objects.create(user=self.staff, gym=self.other_gym, role=Role.PERSON)
        self.client.force_authenticate(self.staff)

        response = self.client.get(reverse('gym-person-list'))
        self.assertEqual(self._emails(response), ['socio@test.com'])

        response = self.client.get(reverse('gym-person-list'), {'gym': self.other_gym.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gyms_show_role_and_only_shared_gyms(self):
        # El staff también es socio del gym ajeno, que el socio consultante no comparte
        GymMembership.objects.create(user=self.staff, gym=self.other_gym, role=Role.PERSON)
        self.client.force_authenticate(self.person)

        response = self.client.get(reverse('gym-staff-list'))

        self.assertEqual(
            response.data[0]['gyms'],
            [{'id': self.gym.id, 'name': 'Gym Centro', 'role': Role.STAFF}],
        )

    def test_gym_filter_must_be_own_gym(self):
        self.client.force_authenticate(self.staff)

        response = self.client.get(reverse('gym-person-list'), {'gym': self.other_gym.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserAdminTests(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(email='root@test.com', password='pass1234')
        self.client.force_login(self.superuser)

    def test_add_and_change_pages_render(self):
        self.assertEqual(self.client.get(reverse('admin:users_user_add')).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('admin:users_user_change', args=[self.superuser.id])).status_code, 200
        )

    def test_can_create_user_with_email(self):
        response = self.client.post(reverse('admin:users_user_add'), {
            'email': 'nuevo@test.com',
            'usable_password': 'true',
            'password1': 'Clave-segura-123',
            'password2': 'Clave-segura-123',
            'memberships-TOTAL_FORMS': '0',
            'memberships-INITIAL_FORMS': '0',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(email='nuevo@test.com').check_password('Clave-segura-123'))


class GymMembershipMigrationTests(TransactionTestCase):
    """users.0002: el rol global de cada usuario pasa a ser el rol en cada uno de sus gimnasios."""

    before = [('users', '0001_initial'), ('gym_tracker', '0007_exercise_description')]
    after = [('users', '0002_gymmembership')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        # Dejar la base con todas las migraciones aplicadas para el resto de los tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_global_role_becomes_role_in_each_gym(self):
        old_apps = self._migrate(self.before)
        OldGym = old_apps.get_model('gym_tracker', 'Gym')
        OldUser = old_apps.get_model('users', 'User')
        centro = OldGym.objects.create(name='Gym Centro')
        norte = OldGym.objects.create(name='Gym Norte')
        staff = OldUser.objects.create(email='staff@test.com', role='STAFF')
        staff.gyms.set([centro, norte])
        OldUser.objects.create(email='sin-gym@test.com', role='ADMIN')

        new_apps = self._migrate(self.after)
        NewGymMembership = new_apps.get_model('users', 'GymMembership')

        self.assertEqual(
            set(NewGymMembership.objects.values_list('user__email', 'gym__name', 'role')),
            {('staff@test.com', 'Gym Centro', 'STAFF'), ('staff@test.com', 'Gym Norte', 'STAFF')},
        )
