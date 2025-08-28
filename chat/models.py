from django.db import models
from django.conf import settings

def make_room(a, b):
    a, b = sorted([int(a), int(b)])
    return f"dm_{a}_{b}"

class Message(models.Model):
    sender    = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
    receiver  = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255, db_index=True)
    content   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [models.Index(fields=["room_name", "timestamp"])]