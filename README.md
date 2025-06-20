# PowerPoint Notes Extraction API

This API extracts slide titles and notes from `.pptx` files. It is built with **FastAPI** and designed to be deployed to **Azure App Service**. It can be invoked from workflows such as **n8n**.

## Features

- **POST `/extract`** – Accepts a JSON payload with `file_url` and `file_name`. The `file_url` should point to a downloadable `.pptx` file while `file_name` will be returned in the response. Returns the slide titles and speaker notes for each slide.
- **POST `/combine`** – Takes a `drive_id`, `folder_id` and `pptx_file_id` and produces an MP4 by downloading the PPTX and slide audio from SharePoint, creating slide images and stitching them together with 2 s crossfades. The resulting video is uploaded back to SharePoint and the URL returned.
- **POST `/html-to-pdf`** and **POST `/html-to-pdf/async`** – Convert raw HTML into a PDF, synchronously or asynchronously.
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

Set `REQUEST_TIMEOUT` to control the read timeout (in seconds) when downloading files (default `60`).
Use `CONNECT_TIMEOUT` to limit how long to wait for an initial connection (default `10`).
`DOWNLOAD_CONCURRENCY` determines how many files are fetched simultaneously (default `5`).

## Running with Docker

Build the container image locally and start it using Docker:

```bash
docker build -t pptx-extractor .
docker run -p 8000:80 pptx-extractor
```

The API will be available at `http://localhost:8000`.
## Testing

Run the unit tests using **pytest**. Install the project's dependencies first:

```bash
pip install -r requirements.txt
pytest
```
## Environment Variables

You can authenticate with Microsoft Graph using either a pre-generated OAuth token or client credentials.

- `GRAPH_TOKEN` (optional): OAuth bearer token for Microsoft Graph.
- `GRAPH_CLIENT_ID`, `GRAPH_TENANT_ID`, `GRAPH_CLIENT_SECRET` (optional): if set, the API obtains a token automatically using the client credentials flow.
- `REQUEST_TIMEOUT` (optional): read timeout in seconds for downloads. Default is `60`.
- `CONNECT_TIMEOUT` (optional): connection timeout in seconds. Default is `10`.
- `DOWNLOAD_CONCURRENCY` (optional): number of files downloaded concurrently. Default is `5`.
- `GUNICORN_TIMEOUT` (optional): worker timeout for Gunicorn in seconds. Default is `300`.
- `FFPROBE_BIN`, `FFMPEG_BIN`, `LIBREOFFICE_BIN` (optional): paths to the
  `ffprobe`, `ffmpeg` and `libreoffice` executables. These override the
  system defaults used by the `/combine` endpoint.


## Deployment

For Azure App Service, configure the startup command with a longer timeout:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -c gunicorn.conf.py extractor_api:app
```

### Using the container image

An image is published to GitHub Container Registry as
`ghcr.io/iius-rcox/pptx-extractor:latest`. To deploy on Azure App Service for
Containers:

1. Set the container image to `ghcr.io/iius-rcox/pptx-extractor:latest`.
2. Leave the startup command empty – the container starts Gunicorn automatically using `gunicorn.conf.py`.
3. Set the application setting `WEBSITE_HEALTHCHECK_PATH=/health` so Azure can
   monitor the API.
4. The container listens on port **80**; ensure any App Service settings or networking rules allow traffic on this port.

## Example Request

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"file_url": "https://example.com/sample.pptx", "file_name": "sample.pptx"}'
```

The response echoes the provided `file_name` as `filename` and returns the total slide count along with an array of slide data containing titles and notes when present.

### Example Combine Request

```bash
# Ensure GRAPH_TOKEN or the client credential variables are set
curl -X POST http://localhost:8000/combine \
  -H "Content-Type: application/json" \
  -d '{"drive_id": "<drive>", "folder_id": "<folder>", "pptx_file_id": "<id>"}'
```

### Example HTML to PDF Request

```bash
curl -X POST http://localhost:8000/html-to-pdf \
  -H "Content-Type: text/plain" \
  --data '<h1>Hello</h1>' \
  -o output.pdf
```

### Example HTML to PDF Async Request

```bash
curl -X POST http://localhost:8000/html-to-pdf/async \
  -H "Content-Type: text/plain" \
  --data '<h1>Hello</h1>' \
  -o output.pdf
```
