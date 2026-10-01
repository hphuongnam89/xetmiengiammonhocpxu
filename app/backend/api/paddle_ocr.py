"""Local Vietnamese OCR adapter backed by PaddleOCR PP-OCRv6."""

import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from django.conf import settings


@lru_cache(maxsize=1)
def _ocr_engine():
    # Keep downloaded OCR models alongside the local app data, never in Git.
    os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(settings.BASE_DIR.parent.parent / ".cache" / "paddlex"))
    from paddleocr import PaddleOCR

    return PaddleOCR(
        device=os.getenv("PADDLE_OCR_DEVICE", "cpu"),
        text_detection_model_name=os.getenv("PADDLE_OCR_DET_MODEL", "PP-OCRv6_tiny_det"),
        text_recognition_model_name=os.getenv("PADDLE_OCR_REC_MODEL", "PP-OCRv6_tiny_rec"),
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )


def _recognize(image_bytes):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as image_file:
        image_file.write(image_bytes)
        image_path = image_file.name
    try:
        result = list(_ocr_engine().predict(image_path))
    finally:
        Path(image_path).unlink(missing_ok=True)
    if not result:
        return "", []
    payload = result[0].json
    data = payload.get("res", payload) if isinstance(payload, dict) else {}
    lines = data.get("rec_texts", []) if isinstance(data, dict) else []
    scores = data.get("rec_scores", []) if isinstance(data, dict) else []
    boxes = data.get("dt_polys", []) if isinstance(data, dict) else []
    records = []
    for index, line in enumerate(lines):
        text = str(line).strip()
        if not text:
            continue
        box = boxes[index] if index < len(boxes) else None
        score = scores[index] if index < len(scores) else 0
        records.append({"text": text, "confidence": float(score or 0), "box": box})
    return "\n".join(item["text"] for item in records), records


def _ollama_fields(raw_text, page_number):
    """Ask the local text model to label OCR spans; OCR text remains the evidence."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_TEXT_MODEL", "ornith1.5:9b")
    prompt = (
        "Extract only fields clearly present in this OCR text from a student academic record. "
        "Do not infer or calculate values. Preserve every course as separate fields. "
        "Return JSON {fields:[{field_key,raw_value,evidence_text,confidence}]} where field_key is one of "
        "student_name,school_name,program,course_name,course_code,grade,credits,document_date. "
        f"All fields come from page {page_number}. OCR text:\n{raw_text[:12000]}"
    )
    import urllib.request

    request = urllib.request.Request(
        f"{base_url}/api/chat",
        data=json.dumps({
            "model": model, "stream": False, "format": "json",
            "think": "low" if model.startswith("gpt-oss") else False,
            "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 4096},
            "messages": [{"role": "user", "content": prompt}],
        }, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read())
    body = json.loads(result["message"]["content"])
    return body.get("fields", []) if isinstance(body, dict) else [], result, model


def extract_images(document, content):
    """OCR every rendered page locally and structure OCR text with a local Ollama model."""
    from .ollama_ocr import _pdf_page_images

    if document.mime_type == "application/pdf":
        from pypdf import PdfReader
        import io

        page_count = len(PdfReader(io.BytesIO(content)).pages)
        images = _pdf_page_images(content, limit=page_count)
    elif document.mime_type in {"image/jpeg", "image/png"}:
        images = [content]
    else:
        raise ValueError("Unsupported OCR document type")

    pages, usage = [], []
    for page_number, image in enumerate(images, start=1):
        raw_text, regions = _recognize(image)
        fields = []
        model = "PaddleOCR/PP-OCRv6"
        if raw_text:
            try:
                fields, result, model = _ollama_fields(raw_text, page_number)
                usage.append({
                    "model": f"{model}+PP-OCRv6",
                    "input_tokens": int(result.get("prompt_eval_count", 0) or 0),
                    "output_tokens": int(result.get("eval_count", 0) or 0),
                })
            except Exception:
                # Preserve OCR output for teacher review even if the local LLM is unavailable.
                pass
        pages.append({
            "page_number": page_number,
            "raw_text": raw_text,
            "fields": fields,
            "regions": regions,
            "ocr_model": model,
        })
    return pages, usage
