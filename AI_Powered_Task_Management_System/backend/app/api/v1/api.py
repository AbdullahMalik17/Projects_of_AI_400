"""
API v1 router aggregation.

Combines all v1 endpoint routers into a single router for inclusion in the main app.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import tasks

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(tasks.router)

# Future endpoint routers will be added here:
# api_router.include_router(chat.router)
# api_router.include_router(analytics.router)
# api_router.include_router(tags.router)
