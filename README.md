# PowerPoint Notes Extraction API

This API extracts slide titles and notes from `.pptx` files. It is built with **FastAPI** and designed to be deployed to **Azure App Service**. It can be invoked from workflows such as **n8n**.

## Features

- **POST `/extract`** – Accepts a JSON payload with `file_url` and `file_name`. The `file_url` should point to a downloadable `.pptx` file while `file_name` will be returned in the response. Returns the slide titles and speaker notes for each slide.
- **POST `/combine`** – Takes a `drive_id`, `folder_id` and `pptx_file_id` and produces an MP4 by downloading the PPTX and slide audio from SharePoint, creating slide images and stitching them together with 2 s crossfades. The resulting video is uploaded back to SharePoint and the URL returned.
- Validation for supported file types and error handling for download/parse failures.
- CORS enabled for testing purposes.
- Suitable for running locally with `uvicorn` or in production with `gunicorn`.

## Requirements

- Python 3.9+
- See `requirements.txt` for Python packages.
- `ffmpeg` and `libreoffice` are required for the `/combine` endpoint.

## Running Locally

```bash
pip install -r requirements.txt
python extractor_api.py  # Runs with uvicorn on port 8000
```

Set `REQUEST_TIMEOUT` to control the download timeout (in seconds). The default
is `60` seconds.
## Environment Variables

- `GRAPH_TOKEN` (required): OAuth bearer token for Microsoft Graph. Export it before running the server, e.g. `export GRAPH_TOKEN=XXXXX`.
- `REQUEST_TIMEOUT` (optional): timeout in seconds when downloading files. Default is `60`.


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

The response echoes the provided `file_name` as `filename` and returns the total slide count along with an array of slide data containing titles and notes when present.

### Example Combine Request

```bash
GRAPH_TOKEN=YOUR_TOKEN curl -X POST http://localhost:8000/combine \
  -H "Content-Type: application/json" \
  -d '{"drive_id": "<drive>", "folder_id": "<folder>", "pptx_file_id": "<id>"}'
```
