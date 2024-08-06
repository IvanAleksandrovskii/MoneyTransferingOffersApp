from fastapi import APIRouter

from .api_views_main import router as api_view_main_router
from .api_views_by_name import router as api_router_by_name
from .api_views_global_objects import router as api_router_global_objects
from .api_views_provider_objects import router as api_router_provider_objects


api_router = APIRouter()
api_router2 = APIRouter()

api_router.include_router(api_view_main_router)
api_router2.include_router(api_router_global_objects)
api_router2.include_router(api_router_provider_objects)
api_router2.include_router(api_router_by_name)

__all__ = ["api_router", "api_router2"]
