from rest_framework import serializers
from .models import Device


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            'id', 'device_name', 'device_identifier',
            'android_version', 'app_version',
            'last_sync_at', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'last_sync_at', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
