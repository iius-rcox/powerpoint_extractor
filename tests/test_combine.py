import subprocess
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import extractor_api

client = TestClient(extractor_api.app)


def _run_factory(images, raise_ffmpeg=False, ffprobe_error=None, raise_libreoffice=False):
    async def _run(cmd):
        if cmd[0] == "ffprobe":
            if ffprobe_error == "file":
                raise FileNotFoundError("ffprobe")
            if ffprobe_error == "process":
                raise subprocess.CalledProcessError(1, cmd)
            return SimpleNamespace(stdout="1.0")
        if cmd[0] == "libreoffice":
            if raise_libreoffice:
                raise FileNotFoundError("libreoffice")
            outdir = cmd[-1]
            for name in images:
                (extractor_api.Path(outdir) / name).write_bytes(b"img")
            return SimpleNamespace()
        if cmd[0] == "ffmpeg":
            if raise_ffmpeg:
                raise FileNotFoundError("ffmpeg")
            extractor_api.Path(cmd[-1]).write_bytes(b"video")
            return SimpleNamespace()
        return SimpleNamespace()

    return _run


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_success(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [
        {"id": "a1", "name": "slide_1.mp3"},
        {"id": "a2", "name": "slide_2.mp3"},
    ]
    mock_run.side_effect = _run_factory(["Slide-1.png", "Slide-2.png"])
    mock_upload.return_value = "http://example.com/video.mp4"

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["video_filename"].endswith(".mp4")
    mock_upload.assert_called_once()


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_slide_names_without_dash(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [
        {"id": "a1", "name": "slide_1.mp3"},
        {"id": "a2", "name": "slide_2.mp3"},
    ]
    mock_run.side_effect = _run_factory(["Slide1.png", "Slide2.png"])
    mock_upload.return_value = "http://example.com/video.mp4"

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    mock_upload.assert_called_once()


@patch("extractor_api.list_folder_children", new_callable=AsyncMock, return_value=[])
@patch(
    "extractor_api.get_item_name", new_callable=AsyncMock, return_value="slides.pptx"
)
@patch(
    "extractor_api.download_file_from_graph",
    new_callable=AsyncMock,
    return_value=b"data",
)
def test_combine_no_mp3(mock_download, mock_get_name, mock_list):
    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "No MP3 files found"


@patch(
    "extractor_api.get_item_name",
    new_callable=AsyncMock,
    side_effect=RuntimeError("fail"),
)
@patch(
    "extractor_api.download_file_from_graph",
    new_callable=AsyncMock,
    return_value=b"data",
)
def test_combine_graph_error(mock_download, mock_get_name):
    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Unable to download PPTX"


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_missing_binary(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [{"id": "a1", "name": "slide_1.mp3"}]
    mock_run.side_effect = _run_factory(["Slide-1.png"], raise_ffmpeg=True)

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "ffmpeg is not installed"


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_ffprobe_error(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [{"id": "a1", "name": "slide_1.mp3"}]
    mock_run.side_effect = _run_factory(["Slide-1.png"], ffprobe_error="process")

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "Audio metadata extraction failed"


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_ffprobe_missing(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [{"id": "a1", "name": "slide_1.mp3"}]
    mock_run.side_effect = _run_factory(["Slide-1.png"], ffprobe_error="file")

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "ffprobe is not installed"


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_libreoffice_missing(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [{"id": "a1", "name": "slide_1.mp3"}]
    mock_run.side_effect = _run_factory(
        ["Slide-1.png"], raise_libreoffice=True
    )

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "libreoffice is not installed"


@patch("extractor_api.upload_file_to_graph", new_callable=AsyncMock)
@patch("extractor_api.run_cmd", new_callable=AsyncMock)
@patch("extractor_api.list_folder_children", new_callable=AsyncMock)
@patch("extractor_api.get_item_name", new_callable=AsyncMock)
@patch("extractor_api.download_file_from_graph", new_callable=AsyncMock)
def test_combine_slide_count_mismatch(
    mock_download, mock_get_name, mock_list, mock_run, mock_upload
):
    mock_download.side_effect = lambda d, i: b"data"
    mock_get_name.return_value = "slides.pptx"
    mock_list.return_value = [
        {"id": "a1", "name": "slide_1.mp3"},
        {"id": "a2", "name": "slide_2.mp3"},
        {"id": "a3", "name": "slide_3.mp3"},
    ]
    mock_run.side_effect = _run_factory(["Slide-1.png", "Slide-2.png"])
    mock_upload.return_value = "http://example.com/video.mp4"

    res = client.post(
        "/combine",
        json={"drive_id": "d", "folder_id": "f", "pptx_file_id": "p"},
    )

    assert res.status_code == 400
    assert res.json()["detail"] == "Slide count mismatch"
