from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient

import extractor_api

client = TestClient(extractor_api.app)


def _setup_graph_mocks(mock_get_name, mock_download, mock_list, mock_upload):
    mock_get_name.return_value = "presentation.pptx"

    def _download_side_effect(drive_id, item_id):
        if item_id == "pptx":
            return b"pptx"
        return b"mp3"

    mock_download.side_effect = _download_side_effect
    mock_list.return_value = [{"name": "slide_1.mp3", "id": "audio1"}]
    mock_upload.return_value = "url"


@patch("extractor_api.upload_file_to_graph")
@patch("extractor_api.list_folder_children")
@patch("extractor_api.download_file_from_graph")
@patch("extractor_api.get_item_name")
@patch("extractor_api.subprocess.run")
def test_ffprobe_missing(mock_run, mock_get_name, mock_download, mock_list, mock_upload):
    _setup_graph_mocks(mock_get_name, mock_download, mock_list, mock_upload)
    mock_run.side_effect = FileNotFoundError()

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "pptx"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "ffprobe not installed"
    mock_run.assert_called_once()


@patch("extractor_api.upload_file_to_graph")
@patch("extractor_api.list_folder_children")
@patch("extractor_api.download_file_from_graph")
@patch("extractor_api.get_item_name")
@patch("extractor_api.subprocess.run")
def test_libreoffice_missing(mock_run, mock_get_name, mock_download, mock_list, mock_upload):
    _setup_graph_mocks(mock_get_name, mock_download, mock_list, mock_upload)
    mock_run.side_effect = [SimpleNamespace(stdout="1"), FileNotFoundError()]

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "pptx"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "libreoffice not installed"
    assert mock_run.call_count == 2


@patch("extractor_api.upload_file_to_graph")
@patch("extractor_api.list_folder_children")
@patch("extractor_api.download_file_from_graph")
@patch("extractor_api.get_item_name")
@patch("extractor_api.subprocess.run")
def test_ffmpeg_missing(mock_run, mock_get_name, mock_download, mock_list, mock_upload):
    _setup_graph_mocks(mock_get_name, mock_download, mock_list, mock_upload)
    mock_run.side_effect = [SimpleNamespace(stdout="1"), None, FileNotFoundError()]

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "pptx"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "ffmpeg not installed"
    assert mock_run.call_count == 3