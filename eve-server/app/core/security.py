# app/core/security.py
from jose import jwt  # 👈 唯一的变化在这里：使用 jose 库里的 jwt
import os
from datetime import datetime, timedelta, timezone

# 读取 .env.development 中的配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "WangJianGuo_Super_Secret_Key_88888888")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 给前端发 7 天有效期的免登录卡

def create_access_token(data: dict) -> str:
    """
    给前端签发 JWT 门禁卡
    """
    to_encode = data.copy()
    
    # 设置过期时间 (UTC 时间)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # 使用你的专属密钥进行签名 (语法和之前一模一样！)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt