from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'user', 'device_identifier', 'last_sync_at', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('device_name', 'device_identifier', 'user__email')
