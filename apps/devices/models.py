import uuid

from django.conf import settings
from django.db import models


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
    )
    device_name = models.CharField(max_length=255)
    device_identifier = models.CharField(max_length=255, unique=True)
    android_version = models.CharField(max_length=50, blank=True, default='')
    app_version = models.CharField(max_length=50, blank=True, default='')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.device_name} ({self.user.email})'
