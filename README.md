# PowerPoint Notes Extraction API

This API extracts slide titles and notes from `.pptx` files. It is built with **FastAPI** and designed to be deployed to **Azure App Service**. It can be invoked from workflows such as **n8n**.

## Features

- **POST `/extract`** – Accepts a JSON payload with `file_url` and `file_name`. The `file_url` should point to a downloadable `.pptx` file while `file_name` will be returned in the response. Returns the slide titles, speaker notes, and the original file content in base64.
- Validation for supported file types and error handling for download/parse failures.
- CORS enabled for testing purposes.
- Suitable for running locally with `uvicorn` or in production with `gunicorn`.

## Requirements

- Python 3.9+
- See `requirements.txt` for Python packages.

## Running Locally

```bash
pip install -r requirements.txt
python extractor_api.py  # Runs with uvicorn on port 8000
```

## Deployment

For Azure App Service, configure the startup command:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker extractor_api:app
```

## Example Request

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"file_url": "https://example.com/sample.pptx", "file_name": "sample.pptx"}'
```

The response echoes the provided `file_name` as `filename`, includes the base64 encoded PowerPoint data in `file_content`, the total slide count, and an array of slide data with titles and notes (if present).
