from django.db import models
from django.utils import timezone
class DeliveryBoy(models.Model):
    name       = models.CharField(max_length=100)
    mobile     = models.CharField(max_length=10, unique=True)
    password   = models.CharField(max_length=128)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.mobile})"