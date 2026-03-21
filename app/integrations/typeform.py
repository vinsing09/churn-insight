"""Typeform API client — placeholder."""
import httpx


class TypeformClient:
    BASE_URL = "https://api.typeform.com"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self._headers = {"Authorization": f"Bearer {access_token}"}

    async def list_forms(self) -> list[dict]:
        """Return all forms owned by the authenticated account."""
        raise NotImplementedError

    async def fetch_responses(self, form_id: str, since: str | None = None) -> list[dict]:
        """Fetch survey responses for a given form, optionally since a timestamp."""
        raise NotImplementedError
