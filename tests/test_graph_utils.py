import httpx
import pytest
from unittest.mock import AsyncMock, patch

import graph_utils

@pytest.mark.asyncio
async def test_download_file_follows_redirects():
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(status_code=200, content=b"data")
    with patch.object(graph_utils, "graph_client", mock_client), \
         patch("graph_utils._auth_headers", new=AsyncMock(return_value={"Authorization": "Bearer t"})):
        result = await graph_utils.download_file_from_graph("d1", "i1")

    mock_client.get.assert_awaited_once_with(
        "https://graph.microsoft.com/v1.0/drives/d1/items/i1/content",
        headers={"Authorization": "Bearer t"},
    )
    assert result == b"data"


@pytest.mark.asyncio
async def test_download_file_multiple_redirects():
    """download_file_from_graph should follow redirect responses manually."""
    mock_client = AsyncMock()
    # first two calls return redirects, final call returns data
    mock_client.get.side_effect = [
        httpx.Response(status_code=302, headers={"location": "https://r1"}),
        httpx.Response(status_code=301, headers={"location": "https://r2"}),
        httpx.Response(status_code=200, content=b"final"),
    ]

    with patch.object(graph_utils, "graph_client", mock_client), patch(
        "graph_utils._auth_headers",
        new=AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        result = await graph_utils.download_file_from_graph("d1", "i1")

    assert result == b"final"
    assert mock_client.get.await_args_list == [
        (("https://graph.microsoft.com/v1.0/drives/d1/items/i1/content",), {
            "headers": {"Authorization": "Bearer t"}
        }),
        (("https://r1",), {"headers": {"Authorization": "Bearer t"}}),
        (("https://r2",), {"headers": {"Authorization": "Bearer t"}}),
    ]
