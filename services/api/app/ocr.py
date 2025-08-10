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
    # Normalize common Swedish currency markers
    norm = text.replace(" kr", "").replace(" KR", "").replace(":-", "")

    # Date patterns: yyyy-mm-dd, dd/mm/yyyy, dd.mm.yyyy, 15 jan 2025
    date_val = None
    # Numeric forms
    m1 = re.search(r"(\d{4}[-\./]\d{2}[-\./]\d{2}|\d{2}[-\./]\d{2}[-\./]\d{4})", norm)
    if m1:
        raw = m1.group(1)
        parts = re.split(r"[-\./]", raw)
        if len(parts[0]) == 4:
            date_val = f"{parts[0]}-{parts[1]}-{parts[2]}"
        else:
            date_val = f"{parts[2]}-{parts[1]}-{parts[0]}"
    else:
        # Swedish month names (short)
        months = {
            "jan": "01", "feb": "02", "mar": "03", "apr": "04", "maj": "05", "jun": "06",
            "jul": "07", "aug": "08", "sep": "09", "okt": "10", "nov": "11", "dec": "12",
        }
        m2 = re.search(r"(\d{1,2})\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)\s+(\d{4})", norm, re.IGNORECASE)
        if m2:
            d, mon, y = m2.groups()
            date_val = f"{y}-{months[mon.lower()]}-{int(d):02d}"

    # Totals: handle 1 234,56 or 1.234,56 or 1234,56 or 1234.56
    # Capture numbers with optional thousand sep (space or dot) and decimal (comma or dot)
    amount_matches = re.findall(r"\b\d{1,3}(?:[ .]\d{3})*[\.,]\d{2}\b|\b\d+[\.,]\d{2}\b", norm)
    parsed: List[float] = []
    for a in amount_matches:
        # Remove spaces and thousands dot when decimal is comma
        if "," in a and "." in a:
            a_norm = a.replace(" ", "").replace(".", "").replace(",", ".")
        else:
            a_norm = a.replace(" ", "").replace(",", ".")
        try:
            parsed.append(float(a_norm))
        except ValueError:
            continue
    total_val = f"{max(parsed):.2f}" if parsed else None

    # Vendor: first non-empty, non-amount line
    lines = [ln.strip() for ln in norm.splitlines() if ln.strip()]
    vendor_val = None
    for ln in lines:
        if not re.search(r"\d", ln) or len(ln.split()) >= 2:
            vendor_val = ln[:100]
            break

    fields: List[Tuple[str, str, float]] = []
    if date_val:
        fields.append(("date", date_val, 0.88))
    if total_val:
        fields.append(("total", total_val, 0.9))
    if vendor_val:
        fields.append(("vendor", vendor_val, 0.75))
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
            from PIL import Image, ImageOps, ImageFilter, ImageEnhance  # type: ignore
            import pytesseract  # type: ignore
            from io import BytesIO
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("pytesseract/Pillow not installed") from e

        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        # Load via OpenCV for deskew/binarization
        data = np.frombuffer(image_bytes, dtype=np.uint8)
        cv = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
        if cv is None:
            image = Image.open(BytesIO(image_bytes))
            cv = np.array(ImageOps.grayscale(image))
        # Binarize using Otsu
        _, th = cv2.threshold(cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Deskew via moments
        coords = np.column_stack(np.where(th > 0))
        angle = 0.0
        if coords.size > 0:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
        (h, w) = th.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(th, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        # Back to PIL for Tesseract
        img = Image.fromarray(rotated)
        # Slight sharpen
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        # Tesseract configuration: Swedish + English, suitable page segmentation
        try:
            text = pytesseract.image_to_string(img, lang="swe+eng", config="--psm 6")
        except Exception:
            text = pytesseract.image_to_string(img)
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

