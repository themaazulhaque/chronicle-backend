from rest_framework import serializers
from .models import InstalledApp, UsageSession


class InstalledAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstalledApp
        fields = (
            'id', 'package_name', 'app_name', 'category',
            'icon_reference', 'is_system_app', 'last_opened_at',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'last_opened_at', 'created_at', 'updated_at')


class UsageSessionSerializer(serializers.ModelSerializer):
    app_name = serializers.CharField(source='installed_app.app_name', read_only=True, default='')

    class Meta:
        model = UsageSession
        fields = (
            'id', 'package_name', 'app_name', 'start_time', 'end_time',
            'duration_seconds', 'source', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class UsageSessionSyncItemSerializer(serializers.Serializer):
    package_name = serializers.CharField(max_length=255)
    app_name = serializers.CharField(max_length=255, required=False, default='')
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    duration_seconds = serializers.IntegerField(min_value=0)


class UsageSyncRequestSerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    sessions = UsageSessionSyncItemSerializer(many=True)

    def validate_device_id(self, value):
        from apps.devices.models import Device
        try:
            device = Device.objects.get(id=value, user=self.context['request'].user)
        except Device.DoesNotExist:
            raise serializers.ValidationError('Device not found or not owned by you.')
        return value


class ActivityQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
    device_id = serializers.UUIDField(required=False)
