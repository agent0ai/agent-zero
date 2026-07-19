"""LiteParse-backed parser for fast local document parsing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from plugins._document_query.helpers.fetch import FetchedDocument
from .base import BaseParser


DEFAULT_OCR_AUTO_DISABLE_PAGES = 30
DEFAULT_OCR_AUTO_SAMPLE_PAGES = 5


@dataclass(frozen=True)
class _PdfTextProfile:
    page_count: int
    sampled_pages: int
    text_chars: int


class LiteParseParser(BaseParser):
    """Fast parser powered by run-llama/liteparse when available."""

    DEFAULT_NUM_WORKERS = 2

    mimetypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "image/",
    ]

    def enabled(self, config: dict) -> bool:
        return bool(config.get("liteparse_enabled", True))

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        # Keep LiteParse native/OCR failures isolated from the Web UI process.
        return self._parse_subprocess(document, config)

    def _parse_in_process(self, document: FetchedDocument, config: dict) -> str:
        try:
            from liteparse import LiteParse
        except Exception as e:
            raise RuntimeError("LiteParse is not installed") from e

        parser = LiteParse(**self._liteparse_kwargs(config))
        with document.local_file() as file_path:
            result = parser.parse(file_path)

        text = getattr(result, "text", "") or ""
        if not text.strip():
            raise ValueError("LiteParse returned no text")
        return text

    def _parse_subprocess(self, document: FetchedDocument, config: dict) -> str:
        with document.local_file() as file_path:
            payload = {
                "file_path": file_path,
                "kwargs": self._liteparse_kwargs(config, document, file_path),
            }
            env = os.environ.copy()
            project_root = str(Path(__file__).resolve().parents[4])
            python_path = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (
                f"{project_root}{os.pathsep}{python_path}"
                if python_path
                else project_root
            )
            timeout = float(config.get("per_document_timeout", 60))
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "plugins._document_query.helpers.parsers.liteparse_worker",
                ],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                cwd=project_root,
                env=env,
                timeout=timeout,
                check=False,
            )

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                "LiteParse subprocess failed"
                f" with exit code {result.returncode}: {detail[-2000:]}"
            )

        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                "LiteParse subprocess returned invalid output: "
                f"{result.stdout[-2000:]}"
            ) from e

        text = response.get("text", "") or ""
        if not text.strip():
            raise ValueError("LiteParse returned no text")
        return text

    def _liteparse_kwargs(
        self,
        config: dict,
        document: FetchedDocument | None = None,
        file_path: str | None = None,
    ) -> dict:
        ocr_enabled = bool(config.get("liteparse_ocr_enabled", True))
        if ocr_enabled and self._should_disable_ocr(config, document, file_path):
            ocr_enabled = False

        kwargs = {
            "ocr_enabled": ocr_enabled,
            "ocr_language": config.get("liteparse_ocr_language", "eng"),
            "max_pages": int(config.get("liteparse_max_pages", 1000)),
            "dpi": float(config.get("liteparse_dpi", 150)),
            "preserve_very_small_text": bool(
                config.get("liteparse_preserve_very_small_text", False)
            ),
            "quiet": True,
        }

        optional_keys = {
            "ocr_server_url": "liteparse_ocr_server_url",
            "target_pages": "liteparse_target_pages",
            "output_format": "liteparse_output_format",
            "password": "liteparse_password",
        }
        for liteparse_key, config_key in optional_keys.items():
            value = config.get(config_key)
            if value not in (None, ""):
                kwargs[liteparse_key] = value

        kwargs["num_workers"] = _positive_int(
            config.get("liteparse_num_workers"),
            self.DEFAULT_NUM_WORKERS,
        )

        tessdata_path = config.get("liteparse_tessdata_path") or _detect_tessdata_path()
        if tessdata_path:
            kwargs["tessdata_path"] = tessdata_path

        return kwargs

    def _should_disable_ocr(
        self,
        config: dict,
        document: FetchedDocument | None,
        file_path: str | None,
    ) -> bool:
        if not bool(config.get("liteparse_ocr_auto_disable", True)):
            return False
        if not document or document.mimetype != "application/pdf" or not file_path:
            return False

        profile = _pdf_text_profile(file_path, config)
        if not profile or profile.sampled_pages <= 0:
            return False

        effective_pages = _effective_page_budget(config, profile.page_count)
        auto_disable_pages = _positive_int(
            config.get("liteparse_ocr_auto_disable_pages"),
            DEFAULT_OCR_AUTO_DISABLE_PAGES,
        )
        if effective_pages < auto_disable_pages:
            return False

        return True


def _pdf_text_profile(file_path: str, config: dict) -> _PdfTextProfile | None:
    try:
        import fitz
    except Exception:
        return None

    try:
        with fitz.open(file_path) as doc:
            page_count = doc.page_count
            if page_count <= 0:
                return _PdfTextProfile(0, 0, 0)
            sample_indexes = _sample_page_indexes(
                page_count=page_count,
                sample_pages=_positive_int(
                    config.get("liteparse_ocr_auto_sample_pages"),
                    DEFAULT_OCR_AUTO_SAMPLE_PAGES,
                ),
                target_pages=config.get("liteparse_target_pages"),
            )
            text_chars = 0
            for page_index in sample_indexes:
                text = doc[page_index].get_text("text") or ""
                text_chars += len("".join(text.split()))
            return _PdfTextProfile(
                page_count=page_count,
                sampled_pages=len(sample_indexes),
                text_chars=text_chars,
            )
    except Exception:
        return None


def _effective_page_budget(config: dict, page_count: int) -> int:
    target_pages = config.get("liteparse_target_pages")
    if target_pages not in (None, ""):
        parsed_target_count = _target_page_count(str(target_pages), page_count)
        if parsed_target_count:
            return parsed_target_count

    max_pages = _positive_int(config.get("liteparse_max_pages"), 1000)
    return min(max_pages, page_count)


def _target_page_count(value: str, page_count: int) -> int:
    pages = _target_page_numbers(value, page_count)
    if pages is None:
        return 0
    return len(pages)


def _target_page_numbers(value: str, page_count: int) -> set[int] | None:
    pages: set[int] = set()
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_raw, end_raw = part.split("-", 1)
            try:
                start = int(start_raw.strip())
                end = int(end_raw.strip())
            except ValueError:
                return None
            if start <= 0 or end <= 0:
                return None
            if start > end:
                start, end = end, start
            pages.update(range(start, min(end, page_count) + 1))
        else:
            try:
                page = int(part)
            except ValueError:
                return None
            if page <= 0:
                return None
            if page <= page_count:
                pages.add(page)
    return pages


def _sample_page_indexes(
    page_count: int,
    sample_pages: int,
    target_pages: str | None = None,
) -> list[int]:
    if page_count <= 0 or sample_pages <= 0:
        return []

    candidate_indexes: list[int]
    if target_pages not in (None, ""):
        target_page_numbers = _target_page_numbers(str(target_pages), page_count)
        if target_page_numbers:
            candidate_indexes = sorted(page - 1 for page in target_page_numbers)
        else:
            candidate_indexes = list(range(page_count))
    else:
        candidate_indexes = list(range(page_count))

    if len(candidate_indexes) <= sample_pages:
        return candidate_indexes

    anchors = [0, 1, 2, len(candidate_indexes) // 2, len(candidate_indexes) - 1]
    indexes = []
    seen = set()
    for anchor in anchors:
        index = candidate_indexes[min(max(anchor, 0), len(candidate_indexes) - 1)]
        if index not in seen:
            seen.add(index)
            indexes.append(index)
        if len(indexes) >= sample_pages:
            break
    return indexes


def _detect_tessdata_path() -> str:
    env_path = os.getenv("TESSDATA_PREFIX", "")
    candidates = [
        env_path,
        "/usr/share/tesseract-ocr/5/tessdata",
        "/usr/share/tesseract-ocr/4.00/tessdata",
        "/usr/share/tessdata",
        "/usr/local/share/tessdata",
    ]
    for candidate in candidates:
        if candidate and (Path(candidate) / "eng.traineddata").is_file():
            return candidate
    return ""


def _positive_int(value, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
