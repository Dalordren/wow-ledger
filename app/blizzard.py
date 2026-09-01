import httpx2
from pydantic import BaseModel
from datetime import datetime, timezone


from app.config import Settings, get_settings

TOKEN_URL = "https://oauth.battle.net/token"
TOKEN_PRICE_PATH = "/data/wow/token/index"
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
        return datetime.fromtimestamp(self.last_updated_timestamp, tz=timezone.utc)


class BlizzardClient:
    """Talks to Blizzard. Nothing else in the app touches httpx2 directly."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_access_token(self) -> str:
        # Set up auth to be passed in client POST
        auth = (
            self._settings.blizzard_client_id,
            self._settings.blizzard_client_secret.get_secret_value(),
        )
        # Open client to route Post
        with httpx2.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(
                TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=auth,
            )
            # Raise status for any errors
            response.raise_for_status()
            # Parse access_token
            token = TokenResponse.model_validate(response.json())
        # return token as string
        return token.access_token

    def get_token_price(self) -> TokenPrice:
        access_token = self.get_access_token()
        region = self._settings.blizzard_region
        api_url = self._settings.blizzard_api_base_url + TOKEN_PRICE_PATH
        params = {"namespace": f"dynamic-{region}", "locale": "en_US"}
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        with httpx2.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(
                api_url,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            wow_token = TokenPrice.model_validate(response.json())
        return wow_token
