from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.devices.models import Device
from .models import InstalledApp, UsageSession
from .serializers import (
    InstalledAppSerializer,
    UsageSessionSerializer,
    UsageSyncRequestSerializer,
)


class AppListView(generics.ListAPIView):
    serializer_class = InstalledAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_devices = Device.objects.filter(user=self.request.user)
        return InstalledApp.objects.filter(device__in=user_devices).order_by('app_name')


class AppDetailView(generics.RetrieveAPIView):
    serializer_class = InstalledAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_devices = Device.objects.filter(user=self.request.user)
        return InstalledApp.objects.filter(device__in=user_devices)


class AppHistoryView(generics.ListAPIView):
    serializer_class = UsageSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_devices = Device.objects.filter(user=self.request.user)
        qs = UsageSession.objects.filter(installed_app__device__in=user_devices)

        app_id = self.kwargs.get('pk')
        if app_id:
            qs = qs.filter(installed_app_id=app_id)

        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(start_time__date__gte=date_from)
        if date_to:
            qs = qs.filter(start_time__date__lte=date_to)

        return qs.order_by('-start_time')


class UsageSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UsageSyncRequestSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        device_id = serializer.validated_data['device_id']
        sessions_data = serializer.validated_data['sessions']

        device = Device.objects.get(id=device_id)
        device.last_sync_at = timezone.now()
        device.save(update_fields=['last_sync_at'])

        created_count = 0
        duplicate_count = 0
        invalid_count = 0

        for session_data in sessions_data:
            try:
                installed_app, _ = InstalledApp.objects.get_or_create(
                    device=device,
                    package_name=session_data['package_name'],
                    defaults={
                        'app_name': session_data.get('app_name', ''),
                    },
                )

                if session_data.get('app_name') and installed_app.app_name != session_data['app_name']:
                    installed_app.app_name = session_data['app_name']
                    installed_app.save(update_fields=['app_name'])

                exists = UsageSession.objects.filter(
                    device=device,
                    package_name=session_data['package_name'],
                    start_time=session_data['start_time'],
                    end_time=session_data['end_time'],
                ).exists()

                if exists:
                    duplicate_count += 1
                    continue

                UsageSession.objects.create(
                    device=device,
                    installed_app=installed_app,
                    package_name=session_data['package_name'],
                    start_time=session_data['start_time'],
                    end_time=session_data['end_time'],
                    duration_seconds=session_data['duration_seconds'],
                    source='system',
                )
                created_count += 1

                if (
                    installed_app.last_opened_at is None
                    or session_data['start_time'] > installed_app.last_opened_at
                ):
                    installed_app.last_opened_at = session_data['start_time']
                    installed_app.save(update_fields=['last_opened_at'])

            except Exception:
                invalid_count += 1

        return Response({
            'created': created_count,
            'duplicates': duplicate_count,
            'invalid': invalid_count,
        }, status=status.HTTP_201_CREATED)


class ActivityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date')
        device_id = request.query_params.get('device_id')

        if not date_str:
            return Response(
                {'error': 'date parameter is required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from datetime import date as date_type
            query_date = date_type.fromisoformat(date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_devices = Device.objects.filter(user=request.user)
        if device_id:
            user_devices = user_devices.filter(id=device_id)

        sessions = UsageSession.objects.filter(
            device__in=user_devices,
            start_time__date=query_date,
        ).select_related('installed_app').order_by('-start_time')

        session_list = []
        for s in sessions:
            session_list.append({
                'id': str(s.id),
                'app_name': s.installed_app.app_name if s.installed_app else s.package_name,
                'package_name': s.package_name,
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'duration_seconds': s.duration_seconds,
            })

        return Response({
            'date': query_date.isoformat(),
            'sessions': session_list,
        })
