from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.devices.models import Device
from apps.usage.models import InstalledApp, UsageSession

User = get_user_model()


class UsageSessionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com', password='pass12345'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com', password='pass12345'
        )
        self.device = Device.objects.create(
            user=self.user,
            device_name='Test Phone',
            device_identifier='device-test-001',
        )
        self.other_device = Device.objects.create(
            user=self.other_user,
            device_name='Other Phone',
            device_identifier='device-other-001',
        )
        self.app = InstalledApp.objects.create(
            device=self.device,
            package_name='com.instagram.android',
            app_name='Instagram',
        )

    def test_session_validation_end_before_start(self):
        session = UsageSession(
            device=self.device,
            installed_app=self.app,
            package_name='com.instagram.android',
            start_time=timezone.now(),
            end_time=timezone.now() - timedelta(hours=1),
            duration_seconds=-3600,
        )
        with self.assertRaises(Exception):
            session.full_clean()

    def test_bulk_sync_creates_sessions(self):
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        data = {
            'device_id': str(self.device.id),
            'sessions': [
                {
                    'package_name': 'com.instagram.android',
                    'app_name': 'Instagram',
                    'start_time': (now - timedelta(hours=2)).isoformat(),
                    'end_time': (now - timedelta(hours=1)).isoformat(),
                    'duration_seconds': 3600,
                },
            ],
        }
        response = self.client.post('/api/v1/usage/sync/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(response.data['duplicates'], 0)

    def test_bulk_sync_duplicate_prevention(self):
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        session_data = {
            'device_id': str(self.device.id),
            'sessions': [
                {
                    'package_name': 'com.instagram.android',
                    'app_name': 'Instagram',
                    'start_time': (now - timedelta(hours=2)).isoformat(),
                    'end_time': (now - timedelta(hours=1)).isoformat(),
                    'duration_seconds': 3600,
                },
            ],
        }
        self.client.post('/api/v1/usage/sync/', session_data, format='json')
        response = self.client.post('/api/v1/usage/sync/', session_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['duplicates'], 1)
        self.assertEqual(response.data['created'], 0)

    def test_sync_other_users_device_rejected(self):
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        data = {
            'device_id': str(self.other_device.id),
            'sessions': [
                {
                    'package_name': 'com.test',
                    'start_time': now.isoformat(),
                    'end_time': now.isoformat(),
                    'duration_seconds': 0,
                },
            ],
        }
        response = self.client.post('/api/v1/usage/sync/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activity_api(self):
        now = timezone.now()
        UsageSession.objects.create(
            device=self.device,
            installed_app=self.app,
            package_name='com.instagram.android',
            start_time=now,
            end_time=now + timedelta(minutes=30),
            duration_seconds=1800,
        )
        self.client.force_authenticate(user=self.user)
        date_str = now.strftime('%Y-%m-%d')
        response = self.client.get(f'/api/v1/usage/activity/?date={date_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['sessions']), 1)

    def test_activity_api_date_filter(self):
        old_time = timezone.now() - timedelta(days=5)
        UsageSession.objects.create(
            device=self.device,
            installed_app=self.app,
            package_name='com.instagram.android',
            start_time=old_time,
            end_time=old_time + timedelta(minutes=30),
            duration_seconds=1800,
        )
        self.client.force_authenticate(user=self.user)
        today = timezone.now().strftime('%Y-%m-%d')
        response = self.client.get(f'/api/v1/usage/activity/?date={today}')
        self.assertEqual(len(response.data['sessions']), 0)

    def test_activity_requires_date(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/usage/activity/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_app_list_scoped_to_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/apps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_app_history_scoped_to_user(self):
        now = timezone.now()
        UsageSession.objects.create(
            device=self.device,
            installed_app=self.app,
            package_name='com.instagram.android',
            start_time=now,
            end_time=now + timedelta(minutes=30),
            duration_seconds=1800,
        )
        UsageSession.objects.create(
            device=self.other_device,
            installed_app=InstalledApp.objects.create(
                device=self.other_device,
                package_name='com.instagram.android',
                app_name='Instagram',
            ),
            package_name='com.instagram.android',
            start_time=now,
            end_time=now + timedelta(minutes=15),
            duration_seconds=900,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/apps/{self.app.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
