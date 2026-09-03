from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.devices.models import Device

User = get_user_model()


class DeviceOwnershipTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com', password='pass12345'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com', password='pass12345'
        )
        self.device1 = Device.objects.create(
            user=self.user1,
            device_name='User1 Phone',
            device_identifier='device-001',
        )
        self.device2 = Device.objects.create(
            user=self.user2,
            device_name='User2 Phone',
            device_identifier='device-002',
        )

    def test_user_cannot_access_other_users_device(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/v1/devices/{self.device2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_access_own_device(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/v1/devices/{self.device1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_only_sees_own_devices(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/v1/devices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_device(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'device_name': 'New Phone',
            'device_identifier': 'device-new-001',
        }
        response = self.client.post('/api/v1/devices/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.filter(user=self.user1).count(), 2)

    def test_unauthenticated_cannot_access_devices(self):
        response = self.client.get('/api/v1/devices/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
