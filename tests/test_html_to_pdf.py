from unittest.mock import patch

from fastapi.testclient import TestClient

import extractor_api

client = TestClient(extractor_api.app)


class DummyHTML:
    def __init__(self, string):
        self.string = string

    def write_pdf(self, target):
        target.write(b"%PDF-1.7")


class FailingHTML(DummyHTML):
    def write_pdf(self, target):
        raise RuntimeError("fail")


def test_html_to_pdf_sync_success():
    with patch("extractor_api.HTML", DummyHTML):
        payload = b"<h1>Hi</h1>"
        res = client.post("/html-to-pdf", data=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")


def test_html_to_pdf_async_success():
    with patch("extractor_api.HTML", DummyHTML):
        payload = b"<h1>Hi</h1>"
        res = client.post("/html-to-pdf/async", data=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")


def test_html_to_pdf_failure():
    with patch("extractor_api.HTML", FailingHTML):
        payload = b"<h1>Hi</h1>"
        res = client.post("/html-to-pdf/async", data=payload)
    assert res.status_code == 500
    assert res.json()["detail"] == "PDF generation failed"
