from fastapi import APIRouter

from app.api.v1.endpoints import assets_router, auth_router, industry_router, market_router, sde_router, universe_router, users_router, wallet_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(industry_router)
api_router.include_router(market_router)
api_router.include_router(sde_router)
api_router.include_router(universe_router)
api_router.include_router(wallet_router)
api_router.include_router(assets_router)