from __future__ import annotations

from io import BytesIO
from pathlib import Path

from api.download_work_dir_file import stream_file_download


def test_stream_file_download_includes_integrity_headers(tmp_path: Path) -> None:
    payload = b"download-payload" * 10_000
    source = tmp_path / "payload.bin"
    source.write_bytes(payload)

    response = stream_file_download(str(source), "payload.bin", chunk_size=4096)

    assert response.headers["Content-Length"] == str(len(payload))
    assert response.headers["X-Content-SHA256"] == (
        "c27444ae06bb85e92d4b8379a5c3f8a46d2ed910aff0c64b87da33544e606cfa"
    )
    assert b"".join(response.response) == payload


def test_stream_file_download_hashes_bytes_io_without_changing_position() -> None:
    payload = b"memory-payload"
    source = BytesIO(payload)
    source.seek(3)

    response = stream_file_download(source, "payload.bin")

    assert response.headers["Content-Length"] == str(len(payload))
    assert response.headers["X-Content-SHA256"] == (
        "125c607bfe36606154f28bcbe339bf05aad4412bb67726651369b22f89dc1102"
    )
    assert b"".join(response.response) == payload
