#!/usr/bin/env python3
"""OCR skeleton for Rgyud-bzhi (四部医典) Root Tantra chapter 20.

Status: SKELETON. Awaits:
  - A scan source (TIFF/PDF) placed under data/scans/rgyud_bzhi/rtsa_rgyud/ch20/
  - A line-crop manifest OR a page-level crop strategy
  - Model credentials (we'll use the OpenClaw image tool for Tibetan OCR;
    local tesseract-bod is a fallback)

The chapter is the primary materia medica locus (per Men-Tsee-Khang 1982 ed.).
Output: data/ocr/rgyud_bzhi_ch20_lines.jsonl
  Each line = {page, line_no, image_crop_path, tibetan_unicode, confidence,
               model, timestamp, review_status: "ai_draft"}

Verification protocol (Sarasvatī-aligned):
  - Every claim about a plant name's presence in ch.20 MUST cite a line_no from this JSONL.
  - Before promoting a plant entry from stub → draft, the OCR text for its name
    must be re-verified against the crop by a second model call (per Sarasvatī rule:
    "every content line in a published artifact must be re-verified by a fresh image call").
"""
from pathlib import Path
import json
import sys
import argparse

ROOT = Path(__file__).resolve().parent.parent
SCANS_DIR = ROOT / "data/scans/rgyud_bzhi/rtsa_rgyud/ch20"
OCR_OUT = ROOT / "data/ocr/rgyud_bzhi_ch20_lines.jsonl"
CROPS_DIR = ROOT / "data/ocr/crops/rgyud_bzhi/ch20"


def check_preconditions():
    issues = []
    if not SCANS_DIR.exists() or not any(SCANS_DIR.iterdir()):
        issues.append(
            f"No scans found at {SCANS_DIR.relative_to(ROOT)}/\n"
            "  Expected: TIFF or PDF of Rgyud-bzhi rtsa-rgyud ch.20.\n"
            "  Candidate sources (Pan to decide):\n"
            "    1. Men-Tsee-Khang 1982 Dharamsala blockprint reprint (PD, Pan may own)\n"
            "    2. Lhasa 1703 Zhol blockprint (if digitized by BDRC — license varies)\n"
            "    3. 内蒙古人民出版社 1982 简体版 (modern typeset, not blockprint — easier OCR, lower provenance)"
        )
    return issues


def plan_crops_from_manifest(manifest_path: Path):
    """Expects a JSON manifest of {page_image, lines: [{line_no, bbox}]} entries."""
    print(f"TODO: implement line-cropping from manifest {manifest_path}")
    print("  Minimum manifest schema:")
    print('    {"page": "0042a.tif", "lines": [{"line_no": 1, "bbox": [x,y,w,h]}, ...]}')


def run_ocr_stub():
    print("Stub mode: OCR engine not yet invoked.")
    print("Planned engines (ordered by precedence):")
    print("  1. OpenClaw image tool (Anthropic vision, prompt-tuned for Uchen Tibetan)")
    print("  2. Google Cloud Vision API (DOCUMENT_TEXT_DETECTION, bod)")
    print("  3. Tesseract 5 + tessdata_best bod.traineddata (fallback)")
    print("  4. Cross-verify by second model call (per Sarasvatī rule)")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Check preconditions and exit")
    parser.add_argument("--plan", action="store_true", help="Plan a crop manifest run")
    args = parser.parse_args()

    issues = check_preconditions()
    if issues:
        print("Preconditions not met:\n", file=sys.stderr)
        for i in issues:
            print(f"  - {i}\n", file=sys.stderr)
        if args.check:
            sys.exit(0)
        sys.exit("Cannot proceed. Rerun with --check for details only.")

    if args.plan:
        plan_crops_from_manifest(SCANS_DIR / "line_manifest.json")
        return
    run_ocr_stub()


if __name__ == "__main__":
    main()
