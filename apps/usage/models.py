import uuid

from django.db import models


class InstalledApp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='installed_apps',
    )
    package_name = models.CharField(max_length=255)
    app_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, default='')
    icon_reference = models.CharField(max_length=255, blank=True, default='')
    is_system_app = models.BooleanField(default=False)
    last_opened_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['app_name']
        unique_together = ['device', 'package_name']

    def __str__(self):
        return f'{self.app_name} ({self.package_name})'


class UsageSession(models.Model):
    SOURCE_CHOICES = [
        ('system', 'System Usage Stats'),
        ('manual', 'Manual Entry'),
        ('import', 'Data Import'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='usage_sessions',
    )
    installed_app = models.ForeignKey(
        InstalledApp,
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        blank=True,
    )
    package_name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_seconds = models.PositiveIntegerField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['device', 'start_time']),
            models.Index(fields=['installed_app', 'start_time']),
            models.Index(fields=['package_name', 'start_time']),
        ]

    def __str__(self):
        return f'{self.package_name} {self.start_time}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValidationError('end_time must not be before start_time')
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValidationError('duration_seconds must be non-negative')
