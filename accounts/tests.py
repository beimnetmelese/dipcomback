from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import User


class ChangePasswordViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='seller@example.com',
            password='oldpass123',
            role=User.Role.SELLER,
            display_name='Seller One',
        )
        self.url = reverse('change-password')

    def test_change_password_requires_correct_current_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                'currentPassword': 'wrong-password',
                'newPassword': 'newpass123',
                'confirmPassword': 'newpass123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.check_password('oldpass123'))

    def test_change_password_updates_password_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                'currentPassword': 'oldpass123',
                'newPassword': 'newpass456',
                'confirmPassword': 'newpass456',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))
