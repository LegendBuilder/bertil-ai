from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


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


class OcrAdapter:
  async def extract(self, image_bytes: bytes) -> OcrResult:  # pragma: no cover - interface
    raise NotImplementedError


class StubOcrAdapter(OcrAdapter):
  async def extract(self, image_bytes: bytes) -> OcrResult:
    # Simple deterministic stub based on size
    size = len(image_bytes)
    text = f"stub-ocr-len:{size}"
    boxes = [
      OcrBox(0.1, 0.1, 0.3, 0.08, "Datum"),
      OcrBox(0.1, 0.22, 0.5, 0.1, "Leverantör"),
      OcrBox(0.6, 0.8, 0.3, 0.12, "Belopp"),
    ]
    fields: List[Tuple[str, str, float]] = [
      ("date", "2025-01-15", 0.92),
      ("total", "123.45", 0.97),
      ("vendor", "Kaffe AB", 0.88),
    ]
    return OcrResult(text=text, boxes=boxes, extracted_fields=fields)


def get_ocr_adapter() -> OcrAdapter:
  # Later: choose Vision/Textract/Tesseract based on ENV
  return StubOcrAdapter()


