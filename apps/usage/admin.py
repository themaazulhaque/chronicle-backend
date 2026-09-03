from django.contrib import admin
from .models import InstalledApp, UsageSession


@admin.register(InstalledApp)
class InstalledAppAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'package_name', 'device', 'last_opened_at')
    list_filter = ('is_system_app',)
    search_fields = ('app_name', 'package_name')


@admin.register(UsageSession)
class UsageSessionAdmin(admin.ModelAdmin):
    list_display = ('package_name', 'device', 'start_time', 'end_time', 'duration_seconds')
    list_filter = ('source', 'start_time')
    search_fields = ('package_name',)
