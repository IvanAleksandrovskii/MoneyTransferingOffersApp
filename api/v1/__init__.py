from fastapi import APIRouter

from .api_views_global_objects import router as global_objects_router
from .api_views_provider_objects import router as provider_objects_router
from .api_main_views import router as main_router


api_router_v1 = APIRouter()

api_router_v1.include_router(main_router, tags=["MAIN"])
api_router_v1.include_router(global_objects_router, prefix="/global-objects", tags=["Global Objects"])
api_router_v1.include_router(provider_objects_router, prefix="/provider-objects", tags=["Provider Objects"])
