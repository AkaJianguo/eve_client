import base64
import logging
import aiohttp
from typing import Dict, Any
from app.core.config import settings
from app.core.errors import api_error


logger = logging.getLogger(__name__)

SSO_USER_AGENT = "WangJianGuo-EVE-SSO/1.0"

class EveSSOService:
    def __init__(self):
        self.client_id = settings.ESI_CLIENT_ID
        self.secret_key = settings.CLIENT_SECRET
        self.token_url = "https://login.eveonline.com/v2/oauth/token"
        self.verify_url = "https://login.eveonline.com/oauth/verify"
        self._session: aiohttp.ClientSession | None = None
        
        if not self.client_id or not self.secret_key:
            raise ValueError("EVE SSO 凭据未在环境变量中配置")
            
        auth_str = f"{self.client_id}:{self.secret_key}"
        self.b64_auth = base64.urlsafe_b64encode(auth_str.encode()).decode()

    def _build_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": SSO_USER_AGENT},
        )

    def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            logger.warning("SSO session was not initialized by app lifespan; creating fallback session")
            self._session = self._build_session()
        return self._session

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = self._build_session()
            logger.info("SSO service session started")

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
            logger.info("SSO service session closed")

    async def _request_token(self, data: Dict[str, str]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Basic {self.b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "login.eveonline.com"
        }
        session = self.get_session()
        
        try:
            async with session.post(self.token_url, headers=headers, data=data) as response:
                if response.status != 200:
                    err = await response.text()
                    logger.warning("SSO token exchange failed: status=%s body=%s", response.status, err)
                    if response.status in {400, 401, 403}:
                        raise api_error(401, "sso_token_invalid", "SSO 授权码或刷新令牌无效，请重新授权")
                    raise api_error(502, "sso_upstream_failed", "EVE SSO 上游服务返回异常，请稍后重试")
                return await response.json()
        except aiohttp.ClientError as exc:
            logger.warning("SSO token request failed: %s", exc)
            raise api_error(503, "sso_upstream_unavailable", "EVE SSO 服务暂时不可用，请稍后重试") from exc

    async def get_access_token(self, code: str) -> Dict[str, Any]:
        """使用 authorization code 换取 Access Token"""
        return await self._request_token(
            {"grant_type": "authorization_code", "code": code}
        )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """使用 refresh_token 换取新的 Access Token。"""
        return await self._request_token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token}
        )

    async def verify_character(self, access_token: str) -> Dict[str, Any]:
        """验证 Token 并获取角色基础信息"""
        headers = {"Authorization": f"Bearer {access_token}"}
        session = self.get_session()
        
        try:
            async with session.get(self.verify_url, headers=headers) as response:
                if response.status != 200:
                    err = await response.text()
                    logger.warning("SSO verify failed: status=%s body=%s", response.status, err)
                    if response.status in {400, 401, 403}:
                        raise api_error(401, "sso_verify_failed", "EVE SSO 令牌验证失败，请重新登录")
                    raise api_error(502, "sso_upstream_failed", "EVE SSO 验证服务返回异常，请稍后重试")
                return await response.json()
        except aiohttp.ClientError as exc:
            logger.warning("SSO verify request failed: %s", exc)
            raise api_error(503, "sso_upstream_unavailable", "EVE SSO 验证服务暂时不可用，请稍后重试") from exc

# 暴露单例
sso_service = EveSSOService()
