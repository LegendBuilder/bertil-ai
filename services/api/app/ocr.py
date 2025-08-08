from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import List, Tuple

from .config import settings


@dataclass
class OcrBox:
    x: float
    y: float
    w: float
    h: float
    label: str


@dataclass
class OcrResult:
    text: str
    boxes: List[OcrBox]
    extracted_fields: List[Tuple[str, str, float]]  # (key, value, confidence)

    def to_json(self) -> str:
        return json.dumps(
            {
                "text": self.text,
                "boxes": [asdict(b) for b in self.boxes],
                "extracted_fields": self.extracted_fields,
            },
            ensure_ascii=False,
        )


class OcrAdapter:
    async def extract(self, image_bytes: bytes) -> OcrResult:  # pragma: no cover - interface
        raise NotImplementedError


def _extract_fields_from_text(text: str) -> List[Tuple[str, str, float]]:
    # Date yyyy-mm-dd or dd/mm/yyyy
    date_match = re.search(r"(\d{4}[-\./]\d{2}[-\./]\d{2}|\d{2}[-\./]\d{2}[-\./]\d{4})", text)
    date_val = None
    if date_match:
        raw_date = date_match.group(1)
        parts = re.split(r"[-\./]", raw_date)
        if len(parts[0]) == 4:
            date_val = f"{parts[0]}-{parts[1]}-{parts[2]}"
        else:
            date_val = f"{parts[2]}-{parts[1]}-{parts[0]}"

    # Totals: pick the largest decimal with 1-2 decimals
    amounts = [float(m.replace(",", ".")) for m in re.findall(r"\d+[\.,]\d{2}", text)]
    total_val = f"{max(amounts):.2f}" if amounts else None

    # Vendor: first non-empty line
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    vendor_val = lines[0][:100] if lines else None

    fields: List[Tuple[str, str, float]] = []
    if date_val:
        fields.append(("date", date_val, 0.85))
    if total_val:
        fields.append(("total", total_val, 0.8))
    if vendor_val:
        fields.append(("vendor", vendor_val, 0.7))
    return fields


class StubOcrAdapter(OcrAdapter):
    async def extract(self, image_bytes: bytes) -> OcrResult:
        size = len(image_bytes)
        text = f"stub-ocr-len:{size}\nKaffe AB\n2025-01-15\n123.45"
        boxes = [
            OcrBox(0.1, 0.1, 0.3, 0.08, "Datum"),
            OcrBox(0.1, 0.22, 0.5, 0.1, "Leverantör"),
            OcrBox(0.6, 0.8, 0.3, 0.12, "Belopp"),
        ]
        fields = _extract_fields_from_text(text)
        return OcrResult(text=text, boxes=boxes, extracted_fields=fields)


class GoogleVisionOcrAdapter(OcrAdapter):
    async def extract(self, image_bytes: bytes) -> OcrResult:  # pragma: no cover - calls external
        try:
            from google.cloud import vision  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("google-cloud-vision not installed/configured") from e

        client_kwargs = {}
        if settings.google_credentials_json_path:
            client_kwargs["credentials"] = None  # Let GOOGLE_APPLICATION_CREDENTIALS env handle
        client = vision.ImageAnnotatorClient(**client_kwargs)
        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)
        if response.error.message:  # pragma: no cover
            raise RuntimeError(f"Vision API error: {response.error.message}")
        text = response.full_text_annotation.text if response.full_text_annotation else (
            response.text_annotations[0].description if response.text_annotations else ""
        )
        boxes = [
            OcrBox(0.1, 0.1, 0.3, 0.08, "Datum"),
            OcrBox(0.1, 0.22, 0.5, 0.1, "Leverantör"),
            OcrBox(0.6, 0.8, 0.3, 0.12, "Belopp"),
        ]
        fields = _extract_fields_from_text(text or "")
        return OcrResult(text=text or "", boxes=boxes, extracted_fields=fields)


class AwsTextractOcrAdapter(OcrAdapter):
    async def extract(self, image_bytes: bytes) -> OcrResult:  # pragma: no cover - calls external
        try:
            import boto3  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("boto3 not installed") from e

        client = boto3.client(
            "textract",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        resp = client.detect_document_text(Document={"Bytes": image_bytes})
        text_lines = [b["Text"] for b in resp.get("Blocks", []) if b.get("BlockType") == "LINE"]
        text = "\n".join(text_lines)
        boxes = [
            OcrBox(0.1, 0.1, 0.3, 0.08, "Datum"),
            OcrBox(0.1, 0.22, 0.5, 0.1, "Leverantör"),
            OcrBox(0.6, 0.8, 0.3, 0.12, "Belopp"),
        ]
        fields = _extract_fields_from_text(text)
        return OcrResult(text=text, boxes=boxes, extracted_fields=fields)


class TesseractOcrAdapter(OcrAdapter):
    async def extract(self, image_bytes: bytes) -> OcrResult:
        try:
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore
            from io import BytesIO
        except Exception as e:  # pragma: no cover
            raise RuntimeError("pytesseract/Pillow not installed") from e

        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        image = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        boxes = [
            OcrBox(0.1, 0.1, 0.3, 0.08, "Datum"),
            OcrBox(0.1, 0.22, 0.5, 0.1, "Leverantör"),
            OcrBox(0.6, 0.8, 0.3, 0.12, "Belopp"),
        ]
        fields = _extract_fields_from_text(text)
        return OcrResult(text=text, boxes=boxes, extracted_fields=fields)


def get_ocr_adapter() -> OcrAdapter:
    provider = (settings.ocr_provider or "stub").lower()
    if provider == "google_vision":
        return GoogleVisionOcrAdapter()
    if provider == "aws_textract":
        return AwsTextractOcrAdapter()
    if provider == "tesseract":
        return TesseractOcrAdapter()
    return StubOcrAdapter()

