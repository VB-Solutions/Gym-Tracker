from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gym_tracker.models import Gym

from .models import User


class GymScopedUserEndpointsTests(APITestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Gym Centro')
        self.other_gym = Gym.objects.create(name='Gym Ajeno')

        self.staff = self._create_user('staff@test.com', User.Role.STAFF, self.gym)
        self.person = self._create_user('socio@test.com', User.Role.PERSON, self.gym)
        self.foreign_staff = self._create_user('staff-ajeno@test.com', User.Role.STAFF, self.other_gym)
        self.foreign_person = self._create_user('socio-ajeno@test.com', User.Role.PERSON, self.other_gym)

    def _create_user(self, email, role, *gyms):
        user = User.objects.create_user(email=email, password='pass1234', role=role)
        user.gyms.set(gyms)
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

    def test_gym_filter_must_be_own_gym(self):
        self.client.force_authenticate(self.staff)

        response = self.client.get(reverse('gym-person-list'), {'gym': self.other_gym.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
