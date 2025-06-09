from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


import httpx

from fastapi.testclient import TestClient

import extractor_api

client = TestClient(extractor_api.app)


def _mock_response(content=b"", headers=None, status_code=200):
    return httpx.Response(
        status_code=status_code, content=content, headers=headers or {}
    )


class DummyPresentation:
    def __init__(self, file_like):
        self.slides = [
            SimpleNamespace(
                shapes=SimpleNamespace(title=SimpleNamespace(text="Title 1")),
                has_notes_slide=True,
                notes_slide=SimpleNamespace(
                    notes_text_frame=SimpleNamespace(text="Notes 1")
                ),
            )
        ]


class FailingPresentation:
    def __init__(self, file_like):
        raise ValueError("bad file")


@patch("extractor_api.HTTPX_TIMEOUT", httpx.Timeout(5))
@patch("extractor_api.TIMEOUT", 5)
@patch("extractor_api.http_client.get", new_callable=AsyncMock)
@patch("extractor_api.Presentation", DummyPresentation)
def test_accepts_pptx_without_extension(mock_presentation, mock_get):
    headers = {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }
    mock_get.return_value = _mock_response(b"content", headers)
    res = client.post(
        "/extract",
        json={"file_url": "https://example.com/file", "file_name": "file.pptx"},
    )
    assert res.status_code == 200
    mock_get.assert_awaited_once_with(
        "https://example.com/file",
        timeout=extractor_api.HTTPX_TIMEOUT,
        follow_redirects=True,
    )
    data = res.json()
    assert data["filename"] == "file.pptx"
    assert "file_content" not in data
    assert data["slide_count"] == 1


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


@patch("extractor_api.HTTPX_TIMEOUT", httpx.Timeout(5))
@patch("extractor_api.TIMEOUT", 5)
@patch("extractor_api.http_client.get", new_callable=AsyncMock)
@patch("extractor_api.Presentation", FailingPresentation)
def test_invalid_pptx_returns_422(mock_presentation, mock_get):
    headers = {"Content-Type": "text/plain"}
    mock_get.return_value = _mock_response(b"bad", headers)
    res = client.post(
        "/extract",
        json={"file_url": "https://example.com/file", "file_name": "file.pptx"},
    )
    assert res.status_code == 422
    assert res.json()["detail"] == "Only .pptx files are supported"
    mock_get.assert_awaited_once_with(
        "https://example.com/file",
        timeout=extractor_api.HTTPX_TIMEOUT,
        follow_redirects=True,
    )

@patch("extractor_api.HTTPX_TIMEOUT", httpx.Timeout(5))
@patch("extractor_api.TIMEOUT", 5)
@patch("extractor_api.http_client.get", new_callable=AsyncMock)
def test_download_http_error(mock_get):
    request = httpx.Request("GET", "https://example.com/file")
    response = _mock_response(status_code=404)
    mock_get.side_effect = httpx.HTTPStatusError("not found", request=request, response=response)
    res = client.post("/extract", json={"file_url": "https://example.com/file", "file_name": "file.pptx"})
    assert res.status_code == 400
    assert "Unable to download file" in res.json()["detail"]
    mock_get.assert_awaited_once_with(
        "https://example.com/file",
        timeout=extractor_api.HTTPX_TIMEOUT,
        follow_redirects=True,
    )


@patch("extractor_api.HTTPX_TIMEOUT", httpx.Timeout(5))
@patch("extractor_api.TIMEOUT", 5)
@patch("extractor_api.http_client.get", new_callable=AsyncMock)
def test_download_request_error(mock_get):
    mock_get.side_effect = httpx.RequestError("boom", request=httpx.Request("GET", "https://example.com/file"))
    res = client.post("/extract", json={"file_url": "https://example.com/file", "file_name": "file.pptx"})
    assert res.status_code == 400
    assert "Unable to download file" in res.json()["detail"]
    mock_get.assert_awaited_once_with(
        "https://example.com/file",
        timeout=extractor_api.HTTPX_TIMEOUT,
        follow_redirects=True,
    )

