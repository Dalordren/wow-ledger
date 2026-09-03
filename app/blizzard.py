from datetime import datetime, timedelta, timezone

import httpx2
from pydantic import BaseModel

from app.config import Settings

TOKEN_URL = "https://oauth.battle.net/token"
TOKEN_PRICE_PATH = "/data/wow/token/index"
TOKEN_EXPIRY_MARGIN_SECONDS = 60
DEFAULT_TIMEOUT = 10.0
COPPER_PER_GOLD = 10_000


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenPrice(BaseModel):
    price: int
    last_updated_timestamp: int

    @property
    def gold(self) -> int:
        return self.price // COPPER_PER_GOLD

    @property
    def updated_at(self) -> datetime:
        seconds = self.last_updated_timestamp / 1000
        return datetime.fromtimestamp(seconds, tz=timezone.utc)


class BlizzardClient:
    """Talks to Blizzard. Nothing else in the app touches httpx2 directly."""

    def __init__(
        self, settings: Settings, transport: httpx2.BaseTransport | None = None
    ) -> None:
        self._settings = settings
        self._transport = transport
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    def get_access_token(self) -> str:
        if (
            self._access_token is not None
            and self._token_expires_at is not None
            and self._token_expires_at > datetime.now(timezone.utc)
        ):
            return self._access_token
        auth = (
            self._settings.blizzard_client_id,
            self._settings.blizzard_client_secret.get_secret_value(),
        )
        with httpx2.Client(
            timeout=DEFAULT_TIMEOUT, transport=self._transport
        ) as client:
            response = client.post(
                TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=auth,
            )
            response.raise_for_status()
            # Parse access_token
            token = TokenResponse.model_validate(response.json())
        self._access_token = token.access_token
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=token.expires_in - TOKEN_EXPIRY_MARGIN_SECONDS
        )

        return self._access_token

    def get_token_price(self) -> TokenPrice:
        access_token = self.get_access_token()
        region = self._settings.blizzard_region
        api_url = self._settings.blizzard_api_base_url + TOKEN_PRICE_PATH
        params = {"namespace": f"dynamic-{region}", "locale": "en_US"}
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        with httpx2.Client(
            timeout=DEFAULT_TIMEOUT, transport=self._transport
        ) as client:
            response = client.get(
                api_url,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            wow_token = TokenPrice.model_validate(response.json())
        return wow_token
