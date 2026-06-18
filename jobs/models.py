from django.db import models
from django.utils import timezone


class JobActivity(models.Model):
    """Celery job activity for the research service."""

    class Status(models.TextChoices):
        PENDING = "PENDING"
        STARTED = "STARTED"
        SUCCESS = "SUCCESS"
        FAILURE = "FAILURE"
        REVOKED = "REVOKED"
        RETRY = "RETRY"
        RECEIVED = "RECEIVED"

    task_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    celery_task = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
    )
    result = models.TextField(null=True, blank=True)
    queue = models.CharField(max_length=128, null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or self.task_id} ({self.status})"

    def mark_status(self, status: str, result: str | None = None):
        self.status = status
        if result is not None:
            self.result = result
        if status in {self.Status.SUCCESS, self.Status.FAILURE, self.Status.REVOKED}:
            self.finished_at = timezone.now()
        self.save(update_fields=["status", "result", "finished_at", "updated_at"])
