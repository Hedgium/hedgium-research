from django.conf import settings
from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI

from analysis.api import router as research_router
from analysis.auth import ResearchAPIKeyAuth

if settings.ENVIRONMENT == "local":
    api = NinjaExtraAPI(title="Hedgium Research API", version="0.1.0")
else:
    api = NinjaExtraAPI(
        title="Hedgium Research API",
        version="0.1.0",
        auth=ResearchAPIKeyAuth(),
    )

api.add_router("research/", research_router, tags=["Research"])

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
