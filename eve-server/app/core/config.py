from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "EVE-Server"
    FRONTEND_URL: str = "http://127.0.0.1:5173"
    WALLET_BALANCE_CACHE_TTL_SECONDS: int = 60
    WALLET_JOURNAL_CACHE_TTL_SECONDS: int = 300
    WALLET_TRANSACTIONS_CACHE_TTL_SECONDS: int = 300
    WALLET_CACHE_WARMUP_ENABLED: bool = True
    WALLET_CACHE_WARMUP_INTERVAL_SECONDS: int = 300
    WALLET_CACHE_WARMUP_BATCH_SIZE: int = 20
    
    # 数据库配置
    # 注意：异步驱动必须使用 postgresql+asyncpg
    DATABASE_URL: str
    
    # EVE ESI 配置 (从 developers.eveonline.com 获取)
    ESI_CLIENT_ID: str
    CLIENT_SECRET: str
    ESI_CALLBACK_URL: str
    
    # JWT 秘钥
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8")

settings = Settings() # type: ignore