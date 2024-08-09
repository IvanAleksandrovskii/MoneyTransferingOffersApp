from fastapi import APIRouter

from .api_main_views import router as main_router
from .api_views_global_objects import router as global_objects_router
from .api_views_provider_objects import router as provider_objects_router
from .api_views_by_name import router as by_name_router
from .api_super_views import router as super_router


api_router = APIRouter()

api_router.include_router(main_router, tags=["MAIN"])
api_router.include_router(super_router, tags=["[WARNING: DEV TOOL, DELETE IT] Super [WARNING: VERY HIGH LOAD]"])
api_router.include_router(global_objects_router, prefix="/global-objects", tags=["Global Objects"])
api_router.include_router(provider_objects_router, prefix="/provider-objects", tags=["Provider Objects"])
api_router.include_router(by_name_router, prefix="/by-name", tags=["By Name [WARNING: HIGH LOAD]"])
