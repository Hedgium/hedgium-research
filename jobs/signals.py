import logging

from celery import signals
from django.utils import timezone

from jobs.models import JobActivity
from jobs.task_logging import logger, task_display_name, truncate_for_log

_db_logger = logging.getLogger(__name__)


def _upsert_job(
    task_id: str,
    status: str,
    name: str | None = None,
    result: str | None = None,
):
    try:
        obj, _created = JobActivity.objects.get_or_create(
            task_id=task_id,
            defaults={"celery_task": name or ""},
        )
        if name:
            obj.celery_task = name
            if not obj.name:
                obj.name = name.rsplit(".", maxsplit=1)[-1].replace("_", "-")

        obj.status = status
        if result is not None:
            obj.result = result
        if status in {
            JobActivity.Status.SUCCESS,
            JobActivity.Status.FAILURE,
            JobActivity.Status.REVOKED,
        }:
            obj.finished_at = timezone.now()
        obj.save()
    except Exception:
        _db_logger.exception("Failed to upsert JobActivity for task_id=%s", task_id)


@signals.task_prerun.connect
def handle_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **_):
    name = task_display_name(task or sender)
    logger.info("Task started: %s (id=%s)", name, task_id)
    _upsert_job(task_id, JobActivity.Status.STARTED, getattr(task, "name", None))


@signals.task_postrun.connect
def handle_task_postrun(sender=None, task_id=None, task=None, retval=None, state=None, **_):
    name = task_display_name(task or sender)
    status = state or JobActivity.Status.SUCCESS
    result_text = truncate_for_log(retval)
    if status == JobActivity.Status.SUCCESS:
        logger.info(
            "Task finished: %s (id=%s) status=%s result=%s",
            name,
            task_id,
            status,
            result_text,
        )
    else:
        logger.warning(
            "Task finished: %s (id=%s) status=%s result=%s",
            name,
            task_id,
            status,
            result_text,
        )
    _upsert_job(
        task_id,
        status,
        getattr(task, "name", None),
        str(retval) if retval else None,
    )


@signals.task_failure.connect
def handle_task_failure(
    task_id=None,
    exception=None,
    sender=None,
    einfo=None,
    **_,
):
    name = task_display_name(sender)
    logger.error(
        "Task failed: %s (id=%s) error=%s",
        name,
        task_id,
        exception,
        exc_info=einfo,
    )
    _upsert_job(
        task_id,
        JobActivity.Status.FAILURE,
        getattr(sender, "name", None),
        str(exception) if exception else None,
    )


@signals.task_retry.connect
def handle_task_retry(sender=None, request=None, reason=None, einfo=None, **_):
    task_id = getattr(request, "id", None)
    name = task_display_name(sender)
    logger.warning(
        "Task retry: %s (id=%s) reason=%s",
        name,
        task_id,
        reason or exception_from_einfo(einfo),
    )


@signals.task_revoked.connect
def handle_task_revoked(
    sender=None,
    request=None,
    terminated=False,
    signum=None,
    expired=False,
    **_,
):
    task_id = getattr(request, "id", None)
    name = task_display_name(sender) if sender else "unknown"
    logger.warning(
        "Task revoked: %s (id=%s) terminated=%s expired=%s",
        name,
        task_id,
        terminated,
        expired,
    )
    if task_id:
        try:
            obj = JobActivity.objects.filter(task_id=task_id).first()
            if obj:
                obj.status = JobActivity.Status.REVOKED
                obj.finished_at = timezone.now()
                obj.save(update_fields=["status", "finished_at", "updated_at"])
        except Exception:
            _db_logger.exception("Failed to mark JobActivity revoked for task_id=%s", task_id)


def exception_from_einfo(einfo) -> str | None:
    if einfo is None:
        return None
    return str(getattr(einfo, "exception", einfo))
