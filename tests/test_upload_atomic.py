from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from api import upload


class _UploadFiles:
    def __init__(self, files: list[object]) -> None:
        self._files = files

    def __contains__(self, key: str) -> bool:
        return key == "file"

    def getlist(self, key: str) -> list[object]:
        return list(self._files) if key == "file" else []


@pytest.mark.asyncio
async def test_upload_streams_atomically_and_returns_integrity_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"0123456789abcdef" * 131_072
    storage = SimpleNamespace(filename="payload.bin", stream=BytesIO(payload))
    monkeypatch.setattr(
        upload.files,
        "get_abs_path",
        lambda *_parts: str(tmp_path / "payload.bin"),
    )
    request = SimpleNamespace(files=_UploadFiles([storage]))

    result = await upload.UploadFile(None, None).process({}, request)

    assert result == {
        "filenames": ["payload.bin"],
        "files": [
            {
                "filename": "payload.bin",
                "size": len(payload),
                "sha256": "9e5c630590af086d064e518b3c1d1cf98e9f4bc9df4fa7cfa32879079a250f62",
            }
        ],
    }
    assert (tmp_path / "payload.bin").read_bytes() == payload
    assert list(tmp_path.glob(".partial-*")) == []


def test_upload_failure_preserves_existing_file_and_removes_partial(tmp_path: Path) -> None:
    target = tmp_path / "payload.bin"
    target.write_bytes(b"original")

    class BrokenStream:
        calls = 0

        def read(self, _size: int) -> bytes:
            self.calls += 1
            if self.calls == 1:
                return b"replacement-prefix"
            raise OSError("simulated upload disconnect")

    storage = SimpleNamespace(stream=BrokenStream())

    with pytest.raises(OSError, match="simulated upload disconnect"):
        upload.save_upload_atomic(storage, str(target))

    assert target.read_bytes() == b"original"
    assert list(tmp_path.glob(".partial-*")) == []
