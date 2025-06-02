import io
import logging
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
logging.basicConfig(level=logging.INFO)


class ExtractRequest(BaseModel):
    file_url: HttpUrl
    file_name: str


class SlideData(BaseModel):
    slide_number: int
    title_text: Optional[str] = None
    notes_text: Optional[str] = None


class ExtractResponse(BaseModel):
    filename: str
    slide_count: int
    slides: List[SlideData]


@app.post("/extract", response_model=ExtractResponse)
def extract_notes(request: ExtractRequest):
    url = request.file_url

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to download file: %s", exc)
        raise HTTPException(status_code=400, detail="Unable to download file") from exc

    content_type = response.headers.get("Content-Type", "")
    if content_type and "presentation" not in content_type and "ppt" not in content_type:
        raise HTTPException(status_code=422, detail="Only .pptx files are supported")

    pptx_bytes = io.BytesIO(response.content)
    try:
        presentation = Presentation(pptx_bytes)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to parse PowerPoint file: %s", exc)
        raise HTTPException(status_code=422, detail="Only .pptx files are supported") from exc

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

    filename = request.file_name
    return ExtractResponse(
        filename=filename,
        slide_count=len(slides_data),
        slides=slides_data,
    )


# For local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
