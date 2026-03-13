from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.industry import router as industry_router
from app.api.v1.endpoints.market import router as market_router
from app.api.v1.endpoints.sde import router as sde_router
from app.api.v1.endpoints.universe import router as universe_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.wallet import router as wallet_router


__all__ = [
    "auth_router",
    "assets_router",
    "users_router",
    "industry_router",
    "market_router",
    "sde_router",
    "universe_router",
    "wallet_router",
]