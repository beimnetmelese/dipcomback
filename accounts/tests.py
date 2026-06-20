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


class SellerPasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role=User.Role.ADMIN,
            display_name='Admin User',
        )
        self.seller = User.objects.create_user(
            email='seller-reset@example.com',
            password='oldpass123',
            role=User.Role.SELLER,
            display_name='Seller Reset',
        )

    def test_admin_can_reset_seller_password(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('sellers-reset-password', kwargs={'pk': self.seller.pk})

        response = self.client.post(
            url,
            {
                'newPassword': 'resetpass456',
                'confirmPassword': 'resetpass456',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.check_password('resetpass456'))
