"""Low-level Jira API client with connection pooling.

This module handles HTTP communication only. No business logic.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import JiraConfig


class JiraAuthError(Exception):
    """Raised when Jira returns 401 or 403."""
    pass


class JiraNotFoundError(Exception):
    """Raised when Jira returns 404."""
    pass


class JiraApiClient:
    """HTTP client for Jira Cloud REST API with connection pooling.
    
    This is a thin wrapper around requests with:
    - Connection pooling for reuse across requests
    - Retry logic for transient failures
    - Consistent error handling
    """

    # Class-level session for connection reuse
    _session: requests.Session | None = None

    def __init__(self, config: JiraConfig) -> None:
        self._config = config
        self._base_url = config.url

    @classmethod
    def _get_session(cls) -> requests.Session:
        """Return a shared session with connection pooling and retry logic."""
        if cls._session is None:
            cls._session = requests.Session()

            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
            )

            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20,
            )
            cls._session.mount("https://", adapter)
            cls._session.mount("http://", adapter)

            cls._session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json",
            })

        return cls._session

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._config.email, self._config.api_token)

    def get(self, endpoint: str, params: dict[str, Any] | None = None, timeout: int = 15) -> dict | list:
        """Execute a GET request.
        
        Args:
            endpoint: API endpoint (e.g., '/rest/api/3/myself')
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Parsed JSON response
            
        Raises:
            JiraAuthError: Invalid credentials
            JiraNotFoundError: Resource not found
            ConnectionError: Network error
            TimeoutError: Request timeout
        """
        url = f"{self._base_url}{endpoint}"
        session = self._get_session()

        try:
            response = session.get(url, auth=self._auth, params=params, timeout=timeout)
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(f"Não foi possível conectar ao Jira ({self._base_url}).") from exc
        except requests.exceptions.Timeout as exc:
            raise TimeoutError(f"Timeout ao conectar ao Jira ({url}).") from exc

        return self._handle_response(response, url)

    def post(self, endpoint: str, body: dict[str, Any], timeout: int = 20) -> dict | list:
        """Execute a POST request.
        
        Args:
            endpoint: API endpoint
            body: Request body (JSON)
            timeout: Request timeout in seconds
            
        Returns:
            Parsed JSON response
        """
        url = f"{self._base_url}{endpoint}"
        session = self._get_session()

        try:
            response = session.post(url, auth=self._auth, json=body, timeout=timeout)
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(f"Não foi possível conectar ao Jira ({self._base_url}).") from exc
        except requests.exceptions.Timeout as exc:
            raise TimeoutError(f"Timeout ao conectar ao Jira ({url}).") from exc

        return self._handle_response(response, url)

    def _handle_response(self, response: requests.Response, url: str) -> dict | list:
        """Handle HTTP response with consistent error handling."""
        if response.status_code in (401, 403):
            raise JiraAuthError("Credenciais inválidas.")
        if response.status_code == 404:
            raise JiraNotFoundError(f"Recurso não encontrado: {url}")

        response.raise_for_status()
        return response.json()

    def test_connection(self) -> dict[str, Any]:
        """Test connection and return current user info."""
        return self.get("/rest/api/3/myself")
