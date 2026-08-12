from pathlib import Path
import zipfile

from api.download_work_dir_file import resolve_download_path
from api.download_work_dir_files import create_selected_zip


def test_download_resolvers_match_file_browser_root(tmp_path: Path) -> None:
    file_path = tmp_path / "outside-a0.txt"
    file_path.write_text("downloadable", encoding="utf-8")

    assert resolve_download_path(str(file_path)) == str(file_path.resolve())

    archive_path = Path(create_selected_zip([str(file_path)], "/"))
    try:
        with zipfile.ZipFile(archive_path) as archive:
            name = str(file_path).lstrip("/")
            assert archive.namelist() == [name]
            assert archive.read(name) == b"downloadable"
    finally:
        archive_path.unlink(missing_ok=True)
