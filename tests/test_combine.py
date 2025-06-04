from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

import extractor_api

client = TestClient(extractor_api.app)


class DummyHTTPError(Exception):
    def __init__(self, status_code=500, message="boom"):
        self.response = SimpleNamespace(status_code=status_code)
        super().__init__(message)


@patch("extractor_api.download_file_from_graph")
def test_download_error_detail_contains_original_message(mock_download):
    mock_download.side_effect = DummyHTTPError(404, "missing")
    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Unable to download PPTX: missing"
    mock_download.assert_called_once_with("d", "p")

