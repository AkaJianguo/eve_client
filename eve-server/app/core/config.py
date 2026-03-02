from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "EVE-Server"
    
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