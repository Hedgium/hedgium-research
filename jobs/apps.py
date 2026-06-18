from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"

    def ready(self):
        from jobs.tasks import agent_tasks, feature_tasks, ingestion_tasks, ml_tasks  # noqa: F401
