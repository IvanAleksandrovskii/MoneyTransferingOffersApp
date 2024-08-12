from fastapi import APIRouter

from api.v1 import api_router_v1

api_router = APIRouter()

api_router.include_router(api_router_v1, prefix="/v1")  # TODO: leave this like that?
