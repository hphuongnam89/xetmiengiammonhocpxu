import base64
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

def _pdf_page_images(content, limit=10):
    executable = os.getenv("PDFTOPPM_BIN") or shutil.which("pdftoppm")
    if not executable:
        raise RuntimeError("pdftoppm is unavailable")
    with tempfile.TemporaryDirectory(prefix="exemption-ocr-") as temp_dir:
        source = Path(temp_dir) / "source.pdf"
        source.write_bytes(content)
        prefix = Path(temp_dir) / "page"
        subprocess.run(
            [executable, "-f", "1", "-l", str(limit), "-jpeg", "-scale-to", "1600", str(source), str(prefix)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=90,
        )
        pages = sorted(Path(temp_dir).glob("page-*.jpg"), key=lambda path: int(path.stem.rsplit("-", 1)[-1]))
        return [path.read_bytes() for path in pages]


def _ollama_page(image_bytes):
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_VISION_MODEL", "ornith-1.5:9b")
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "think": "low" if model.startswith("gpt-oss") else False,
        "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 6144},
        "messages": [{"role": "user", "content": "Đọc chính xác trang tài liệu tiếng Việt/Anh. Không suy đoán. Trả JSON: {raw_text:string, fields:[{field_key,raw_value,evidence_text,confidence}]} . confidence từ 0 đến 1.", "images": [base64.b64encode(image_bytes).decode("ascii")]}],
    }
    request = urllib.request.Request(
        f"{base_url}/api/chat", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read())
    if result.get("done_reason") == "length":
        raise ValueError("OCR response was truncated")
    body = json.loads(result["message"]["content"])
    return body, result, model


def extract_images(document, content):
    if document.mime_type == "application/pdf":
        import io
        from pypdf import PdfReader
        images = _pdf_page_images(content, limit=len(PdfReader(io.BytesIO(content)).pages))
    elif document.mime_type in {"image/jpeg", "image/png"}:
        images = [content]
    else:
        raise ValueError("Unsupported OCR document type")
    pages, usage = [], []
    for page_number, image in enumerate(images, start=1):
        body, result, model = _ollama_page(image)
        pages.append({"page_number": page_number, "raw_text": str(body.get("raw_text", "")), "fields": body.get("fields", [])})
        usage.append({
            "model": model,
            "input_tokens": int(result.get("prompt_eval_count", 0) or 0),
            "output_tokens": int(result.get("eval_count", 0) or 0),
        })
    return pages, usage
