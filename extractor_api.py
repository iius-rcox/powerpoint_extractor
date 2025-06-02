import io
import logging
import base64
import os
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from pptx import Presentation


app = FastAPI(title="PowerPoint Notes Extraction API")

# Enable CORS for all origins (use more restrictive settings in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("pptx_extractor")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# Allow the request timeout to be configured via an environment variable.
# Defaults to 10 seconds if not provided.
TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "10"))


class ExtractRequest(BaseModel):
    file_url: HttpUrl
    file_name: str


class SlideData(BaseModel):
    slide_number: int
    title_text: Optional[str] = None
    notes_text: Optional[str] = None


class ExtractResponse(BaseModel):
    filename: str
    file_content: str
    slide_count: int
    slides: List[SlideData]


@app.post("/extract", response_model=ExtractResponse)
def extract_notes(request: ExtractRequest):
    url = request.file_url
    logger.info("Extraction requested for %s", url)

    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        logger.debug("Downloaded %d bytes", len(response.content))
    except requests.RequestException as exc:
        logger.exception("Failed to download file from %s", url)
        raise HTTPException(status_code=400, detail=f"Unable to download file: {exc}") from exc

    content_type = response.headers.get("Content-Type", "")
    logger.debug("Content-Type received: %s", content_type)
    if content_type and "presentation" not in content_type and "ppt" not in content_type:
        logger.warning("Unsupported content type: %s", content_type)
        raise HTTPException(status_code=422, detail="Only .pptx files are supported")

    pptx_bytes = io.BytesIO(response.content)
    file_content = base64.b64encode(response.content).decode("utf-8")
    try:
        presentation = Presentation(pptx_bytes)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to parse PowerPoint file")
        raise HTTPException(status_code=422, detail="Invalid .pptx file") from exc

    slides_data: List[SlideData] = []
    for idx, slide in enumerate(presentation.slides, start=1):
        title = None
        if slide.shapes.title is not None:
            title = slide.shapes.title.text

        notes_text = None
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes_text = slide.notes_slide.notes_text_frame.text

        slides_data.append(
            SlideData(
                slide_number=idx,
                title_text=title,
                notes_text=notes_text,
            )
        )

    logger.info("Successfully extracted %d slides", len(slides_data))

    filename = request.file_name
    return ExtractResponse(
        filename=filename,
        file_content=file_content,
        slide_count=len(slides_data),
        slides=slides_data,
    )


# For local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
