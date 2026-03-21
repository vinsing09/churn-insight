"""Delighted API client — placeholder."""
import httpx


class DelightedClient:
    BASE_URL = "https://api.delighted.com/v1"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._auth = (api_key, "")

    async def fetch_survey_responses(self, since: int | None = None) -> list[dict]:
        """Fetch NPS survey responses. `since` is a Unix timestamp."""
        raise NotImplementedError
