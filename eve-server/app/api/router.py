from fastapi import APIRouter

from app.api.v1 import api_router as v1_router
from app.api.v2 import api_router as v2_router


api_router = APIRouter()
api_router.include_router(v1_router)
api_router.include_router(v2_router)