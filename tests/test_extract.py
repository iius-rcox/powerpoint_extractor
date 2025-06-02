import sys
from types import SimpleNamespace, ModuleType
from unittest.mock import patch


class _StubResponse:
    def __init__(self):
        self.status_code = 200
        self._content = b""
        self.headers = {}

    @property
    def content(self):
        return self._content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException("error")


class RequestException(Exception):
    pass


def _get(*_, **__):
    return _StubResponse()


requests = ModuleType("requests")
requests.Response = _StubResponse
requests.RequestException = RequestException
requests.get = _get
sys.modules.setdefault("requests", requests)

from fastapi.testclient import TestClient

import extractor_api

client = TestClient(extractor_api.app)


def _mock_response(content=b"", headers=None, status_code=200):
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = content
    resp.headers = headers or {}
    return resp


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


@patch("extractor_api.TIMEOUT", 5)
@patch("extractor_api.requests.get")
@patch("extractor_api.Presentation", DummyPresentation)
def test_accepts_pptx_without_extension(mock_get):
    headers = {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }
    mock_get.return_value = _mock_response(b"content", headers)
    res = client.post(
        "/extract",
        json={"file_url": "https://example.com/file", "file_name": "file.pptx"},
    )
    assert res.status_code == 200
    mock_get.assert_called_once_with("https://example.com/file", timeout=5)
    data = res.json()
    assert data["filename"] == "file.pptx"
    assert "file_content" not in data
    assert data["slide_count"] == 1


@patch("extractor_api.TIMEOUT", 5)
@patch("extractor_api.requests.get")
@patch("extractor_api.Presentation", FailingPresentation)
def test_invalid_pptx_returns_422(mock_get):
    headers = {"Content-Type": "text/plain"}
    mock_get.return_value = _mock_response(b"bad", headers)
    res = client.post(
        "/extract",
        json={"file_url": "https://example.com/file", "file_name": "file.pptx"},
    )
    assert res.status_code == 422
    assert res.json()["detail"] == "Only .pptx files are supported"
    mock_get.assert_called_once_with("https://example.com/file", timeout=5)
