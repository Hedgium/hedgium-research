from ninja.security import APIKeyHeader
from django.conf import settings


class ResearchAPIKeyAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        expected = settings.RESEARCH_API_KEY
        if not expected:
            return None
        if key == expected:
            return key
        return None
