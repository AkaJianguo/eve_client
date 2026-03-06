from fastapi import APIRouter

from app.api.v1.endpoints import auth_router, industry_router, universe_router, users_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(industry_router)
api_router.include_router(universe_router)