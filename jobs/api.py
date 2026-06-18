"""Admin API for triggering and monitoring Celery jobs."""

from __future__ import annotations

import logging
from typing import Any

from celery import current_app
from celery.result import AsyncResult
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from ninja import Router, Schema

from jobs.models import JobActivity

logger = logging.getLogger(__name__)

router = Router()

MANUAL_TASKS: dict[str, dict[str, str]] = {
    "ingest-ohlcv-kite-only": {
        "task": "jobs.tasks.ingestion_tasks.ingest_ohlcv_kite_only",
        "schedule": "Manual",
    },
    "ingest-fii-dii": {
        "task": "jobs.tasks.ingestion_tasks.ingest_fii_dii_daily",
        "schedule": "Manual",
    },
    "ingest-sector-performance": {
        "task": "jobs.tasks.ingestion_tasks.compute_sector_performance_daily",
        "schedule": "Manual",
    },
    "ingest-corporate-events": {
        "task": "jobs.tasks.ingestion_tasks.ingest_corporate_events_task",
        "schedule": "Manual",
    },
}


def _task_registry() -> dict[str, dict[str, str]]:
    registry: dict[str, dict[str, str]] = {}
    for name, config in settings.CELERY_BEAT_SCHEDULE.items():
        registry[name] = {
            "task": config["task"],
            "schedule": str(config.get("schedule", "Beat")),
        }
    registry.update(MANUAL_TASKS)
    return registry


class StopTaskSchema(Schema):
    task_id: str
    terminate: bool = True


@router.get("/")
def list_scheduled_tasks(request):
    tasks: list[dict[str, str]] = []
    for name, config in _task_registry().items():
        tasks.append(
            {
                "name": name,
                "task": config.get("task", ""),
                "schedule": config.get("schedule", "Unknown"),
            }
        )
    tasks.sort(key=lambda row: row["name"])
    return tasks


@router.post("run/")
def run_task(request, task_name: str):
    registry = _task_registry()
    if task_name not in registry:
        return JsonResponse(
            {"error": f"Task '{task_name}' not found"},
            status=404,
        )

    task_path = registry[task_name].get("task")
    if not task_path:
        return JsonResponse({"error": "Task path not defined"}, status=400)

    try:
        result = current_app.send_task(task_path)
        JobActivity.objects.update_or_create(
            task_id=result.id,
            defaults={
                "name": task_name,
                "celery_task": task_path,
                "status": JobActivity.Status.PENDING,
                "started_at": timezone.now(),
            },
        )
        logger.info("Manually triggered research task %s (id=%s)", task_name, result.id)
        return {
            "status": "success",
            "message": f"Task '{task_name}' triggered successfully",
            "task_id": result.id,
        }
    except Exception as exc:
        logger.exception("Error triggering research task %s", task_name)
        return JsonResponse({"error": str(exc)}, status=500)


@router.get("running/")
def list_running_tasks(request):
    running_statuses = [
        JobActivity.Status.PENDING,
        JobActivity.Status.STARTED,
        JobActivity.Status.RETRY,
        JobActivity.Status.RECEIVED,
    ]

    activities = JobActivity.objects.filter(status__in=running_statuses).order_by(
        "-started_at"
    )

    output: list[dict[str, Any]] = []
    for activity in activities:
        result = AsyncResult(activity.task_id)
        activity.mark_status(
            result.status,
            str(result.result) if result.result else None,
        )
        if activity.status not in running_statuses:
            continue
        output.append(
            {
                "task_id": activity.task_id,
                "name": activity.name or activity.celery_task or "unknown",
                "status": activity.status,
                "queue": activity.queue,
                "started_at": activity.started_at.isoformat()
                if activity.started_at
                else None,
                "finished_at": activity.finished_at.isoformat()
                if activity.finished_at
                else None,
            }
        )

    return output


@router.post("stop/")
def stop_task(request, payload: StopTaskSchema):
    activity = JobActivity.objects.filter(task_id=payload.task_id).first()
    try:
        current_app.control.revoke(payload.task_id, terminate=payload.terminate)
    except Exception as exc:
        logger.exception("Failed to revoke task %s", payload.task_id)
        return JsonResponse({"error": str(exc)}, status=500)

    if activity:
        activity.status = JobActivity.Status.REVOKED
        activity.finished_at = timezone.now()
        activity.save(update_fields=["status", "finished_at", "updated_at"])

    return {
        "task_id": payload.task_id,
        "status": "REVOKED",
        "message": f"Task {payload.task_id} revoked",
    }
