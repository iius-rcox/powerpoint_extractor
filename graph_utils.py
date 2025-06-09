"""Helper functions for interacting with Microsoft Graph API."""

from __future__ import annotations

import os
import time
from typing import Iterable, Dict, Optional
import asyncio

import httpx

GRAPH_BASE_URL = os.environ.get("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "60"))
CONNECT_TIMEOUT = float(os.environ.get("CONNECT_TIMEOUT", "10"))

# Shared HTTP client for Graph requests
graph_client: Optional[httpx.AsyncClient] = None


async def startup_graph_client() -> None:
    """Create the HTTP client used for Graph requests.

    The default connection pool limit of ``httpx.AsyncClient`` is ``100``. When
    downloading many audio files concurrently this limit can be exceeded which
    results in ``PoolTimeout`` errors. To avoid this we create the client with
    an unlimited connection pool.
    """
    global graph_client
    limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)
    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=REQUEST_TIMEOUT,
        write=REQUEST_TIMEOUT,
        pool=CONNECT_TIMEOUT,
    )
    graph_client = httpx.AsyncClient(limits=limits, timeout=timeout)


async def close_graph_client() -> None:
    """Close the Graph HTTP client if it exists."""
    global graph_client
    if graph_client is not None:
        await graph_client.aclose()

_cached_token: Optional[str] = None
_token_expiry: float = 0.0


async def _get_token() -> str:
    """Return a valid access token for Microsoft Graph."""
    global _cached_token, _token_expiry

    # Reuse token if it's still valid for at least 1 minute
    if _cached_token and time.time() < _token_expiry - 60:
        return _cached_token

    env_token = os.getenv("GRAPH_TOKEN")
    if env_token:
        _cached_token = env_token
        _token_expiry = time.time() + 3600
        return _cached_token

    client_id = os.getenv("GRAPH_CLIENT_ID")
    tenant_id = os.getenv("GRAPH_TENANT_ID")
    client_secret = os.getenv("GRAPH_CLIENT_SECRET")

    if not all([client_id, tenant_id, client_secret]):
        raise RuntimeError("Graph credentials not configured")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    response = await graph_client.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
    )
    response.raise_for_status()
    data = response.json()
    _cached_token = data["access_token"]
    _token_expiry = time.time() + int(data.get("expires_in", 3600))
    return _cached_token


async def _auth_headers() -> Dict[str, str]:
    token = await _get_token()
    return {"Authorization": f"Bearer {token}"}


async def download_file_from_graph(drive_id: str, item_id: str, retries: int = 3) -> bytes:
    """Return the file content for the given drive and item.

    This function manually follows redirects. Some environments or older
    versions of ``httpx`` may not respect the ``follow_redirects`` flag,
    resulting in ``HTTPStatusError`` for 302 responses. To ensure the file is
    downloaded reliably we iterate through up to 5 redirects ourselves.
    """

    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{item_id}/content"
    headers = await _auth_headers()

    for attempt in range(retries):
        next_url = url
        try:
            for _ in range(5):
                response = await graph_client.get(next_url, headers=headers)
                if response.is_redirect:
                    next_url = response.headers.get("location")
                    if not next_url:
                        response.raise_for_status()
                    continue
                response.raise_for_status()
                return response.content
            response.raise_for_status()
        except httpx.RequestError:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)

    # Retries exhausted
    raise httpx.HTTPError("Max retries exceeded")


async def upload_file_to_graph(
    drive_id: str, folder_id: str, filename: str, content: bytes
) -> str:
    """Upload binary content and return the resulting file web URL."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{folder_id}:/{filename}:/content"
    response = await graph_client.put(url, headers=await _auth_headers(), data=content)
    response.raise_for_status()
    data = response.json()
    # The Graph API returns the uploaded item metadata including a ``webUrl`` key
    return data.get("webUrl", "")


async def list_folder_children(
    drive_id: str, folder_id: str
) -> Iterable[Dict[str, str]]:
    """Return metadata for items within the folder."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{folder_id}/children"
    response = await graph_client.get(url, headers=await _auth_headers())
    response.raise_for_status()
    data = response.json()
    return data.get("value", [])


async def get_item_name(drive_id: str, item_id: str) -> str:
    """Return the file name for the given item."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{item_id}"
    response = await graph_client.get(url, headers=await _auth_headers())
    response.raise_for_status()
    data = response.json()
    return data.get("name", "")
