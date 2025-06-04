"""Helper functions for interacting with Microsoft Graph API."""

from __future__ import annotations

import os
from typing import Iterable, Dict, List

import requests

GRAPH_BASE_URL = os.environ.get("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")


def _auth_headers() -> Dict[str, str]:
    token = os.getenv("GRAPH_TOKEN")
    if not token:
        raise RuntimeError("GRAPH_TOKEN environment variable not set")
    return {"Authorization": f"Bearer {token}"}


def download_file_from_graph(drive_id: str, item_id: str) -> bytes:
    """Return the file content for the given drive and item."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{item_id}/content"
    response = requests.get(url, headers=_auth_headers())
    response.raise_for_status()
    return response.content


def upload_file_to_graph(drive_id: str, folder_id: str, filename: str, content: bytes) -> str:
    """Upload binary content and return the resulting file web URL."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{folder_id}:/{filename}:/content"
    response = requests.put(url, headers=_auth_headers(), data=content)
    response.raise_for_status()
    data = response.json()
    # The Graph API returns the uploaded item metadata including a ``webUrl`` key
    return data.get("webUrl", "")


def list_folder_children(drive_id: str, folder_id: str) -> Iterable[Dict[str, str]]:
    """Return metadata for items within the folder."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{folder_id}/children"
    response = requests.get(url, headers=_auth_headers())
    response.raise_for_status()
    data = response.json()
    return data.get("value", [])


def get_item_name(drive_id: str, item_id: str) -> str:
    """Return the file name for the given item."""
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{item_id}"
    response = requests.get(url, headers=_auth_headers())
    response.raise_for_status()
    data = response.json()
    return data.get("name", "")
