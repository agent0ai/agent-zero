import os
from pathlib import Path
import shutil
import base64
import subprocess
from typing import Dict, List, Tuple, Any
from helpers.security import safe_filename
from datetime import datetime

from helpers import files
from helpers.localization import Localization
from helpers.print_style import PrintStyle


class FileBrowser:
    ALLOWED_EXTENSIONS = {
        'image': {'jpg', 'jpeg', 'png', 'bmp'},
        'code': {'py', 'js', 'sh', 'html', 'css'},
        'document': {'md', 'pdf', 'txt', 'csv', 'json'}
    }

    @classmethod
    def max_file_bytes(cls):
        from helpers.settings import get_settings
        return get_settings()["file_browser_max_transfer_size_mb"] * 1024 * 1024

    @classmethod
    def max_text_bytes(cls):
        from helpers.settings import get_settings
        return get_settings()["file_browser_max_text_size_mb"] * 1024 * 1024

    @classmethod
    def limits(cls):
        return {"max_file_bytes": cls.max_file_bytes(), "max_text_bytes": cls.max_text_bytes()}

    @classmethod
    def decode_text(cls, data: bytes) -> str:
        limit = cls.max_text_bytes()
        if len(data) > limit:
            raise ValueError(f"Text files are limited to {limit / (1024 * 1024):g} MiB.")
        if files.is_probably_binary_bytes(data):
            raise ValueError("Binary file detected; editing is not supported")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Unable to decode file as UTF-8; editing is not supported") from error

    @classmethod
    def text_bytes(cls, content: str) -> bytes:
        data = content.encode("utf-8")
        cls.decode_text(data)
        return data

    def __init__(self):
        # if runtime.is_development():
        #     base_dir = files.get_base_dir()
        # else:
        #     base_dir = "/"
        base_dir = "/"
        self.base_dir = Path(base_dir)

    def _check_file_size(self, file) -> bool:
        try:
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            return size <= self.max_file_bytes()
        except (AttributeError, IOError):
            return False

    def save_file_b64(self, current_path: str, filename: str, base64_content: str):
        try:
            # Resolve the target directory path
            target_file = (self.base_dir / current_path / filename).resolve()
            if not str(target_file).startswith(str(self.base_dir)):
                raise ValueError("Invalid target directory")

            os.makedirs(target_file.parent, exist_ok=True)
            content = base64.b64decode(base64_content)
            if len(content) > self.max_file_bytes():
                raise ValueError("File exceeds the transfer size limit.")
            # Save file
            with open(target_file, "wb") as file:
                file.write(content)
            return True
        except Exception as e:
            PrintStyle.error(f"Error saving file {filename}: {e}")
            return False

    def save_files(self, files: List, current_path: str = "") -> Tuple[List[str], List[str]]:
        """Save uploaded files and return successful and failed filenames"""
        successful = []
        failed = []

        try:
            # Resolve the target directory path
            target_dir = (self.base_dir / current_path).resolve()
            if not str(target_dir).startswith(str(self.base_dir)):
                raise ValueError("Invalid target directory")

            os.makedirs(target_dir, exist_ok=True)

            for file in files:
                try:
                    if file and self._is_allowed_file(file.filename, file) and self._check_file_size(file):
                        filename = safe_filename(file.filename)
                        if not filename:
                            raise ValueError("Invalid filename")
                        file_path = target_dir / filename

                        file.save(str(file_path))
                        successful.append(filename)
                    else:
                        failed.append(file.filename)
                except Exception as e:
                    PrintStyle.error(f"Error saving file {file.filename}: {e}")
                    failed.append(file.filename)

            return successful, failed

        except Exception as e:
            PrintStyle.error(f"Error in save_files: {e}")
            return successful, failed

    def delete_file(self, file_path: str) -> bool:
        """Delete a file or empty directory"""
        try:
            # Resolve the full path while preventing directory traversal
            full_path = (self.base_dir / file_path).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid path")

            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                return True

            return False

        except Exception as e:
            PrintStyle.error(f"Error deleting {file_path}: {e}")
            return False

    def rename_item(self, file_path: str, new_name: str) -> bool:
        try:
            if not new_name or new_name in {".", ".."}:
                raise ValueError("Invalid new name")
            if "/" in new_name or "\\" in new_name:
                raise ValueError("New name cannot include path separators")

            full_path = (self.base_dir / file_path).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid path")
            if not full_path.exists():
                raise FileNotFoundError("File or folder not found")

            new_path = full_path.with_name(new_name)
            if not str(new_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid target path")
            if full_path == new_path:
                return True
            if new_path.exists():
                raise FileExistsError("Target already exists")

            os.rename(full_path, new_path)
            return True
        except Exception as e:
            PrintStyle.error(f"Error renaming {file_path}: {e}")
            raise

    def move_items(self, file_paths: List[str], destination_path: str) -> List[str]:
        if not file_paths:
            raise ValueError("No items selected")

        base_dir = self.base_dir.resolve()
        destination = (self.base_dir / destination_path).resolve()
        if not destination.is_relative_to(base_dir):
            raise ValueError("Invalid destination path")
        if not destination.is_dir():
            raise NotADirectoryError("Destination folder not found")

        moves: List[Tuple[Path, Path]] = []
        targets: set[Path] = set()
        for file_path in dict.fromkeys(file_paths):
            requested = self.base_dir / file_path
            source = requested.parent.resolve() / requested.name
            if not source.is_relative_to(base_dir) or source == base_dir:
                raise ValueError("Invalid source path")
            if not source.exists() and not source.is_symlink():
                raise FileNotFoundError(f"Item not found: {source.name}")
            if source == destination:
                raise ValueError("A folder cannot be moved into itself")
            if (
                source.is_dir()
                and not source.is_symlink()
                and destination.is_relative_to(source)
            ):
                raise ValueError("A folder cannot be moved into itself")

            target = destination / source.name
            if target == source:
                raise ValueError(f"{source.name} is already in this folder")
            if target.exists() or target.is_symlink():
                raise FileExistsError(
                    f'An item named "{source.name}" already exists'
                )
            if target in targets:
                raise FileExistsError(f'Multiple items are named "{source.name}"')
            targets.add(target)
            moves.append((source, target))

        moved: List[Tuple[Path, Path]] = []
        try:
            for source, target in moves:
                os.rename(source, target)
                moved.append((source, target))
        except Exception:
            for source, target in reversed(moved):
                try:
                    os.rename(target, source)
                except Exception as rollback_error:
                    PrintStyle.error(f"Error restoring {source}: {rollback_error}")
            raise

        return [str(target) for _, target in moved]

    def create_folder(self, parent_path: str, folder_name: str) -> bool:
        try:
            if not folder_name or folder_name in {".", ".."}:
                raise ValueError("Invalid folder name")
            if "/" in folder_name or "\\" in folder_name:
                raise ValueError("Folder name cannot include path separators")

            parent_full = (self.base_dir / parent_path).resolve()
            if not str(parent_full).startswith(str(self.base_dir)):
                raise ValueError("Invalid parent path")

            target_dir = (parent_full / folder_name).resolve()
            if not str(target_dir).startswith(str(self.base_dir)):
                raise ValueError("Invalid target path")
            if target_dir.exists():
                raise FileExistsError("Folder already exists")

            os.makedirs(target_dir, exist_ok=False)
            return True
        except Exception as e:
            PrintStyle.error(f"Error creating folder {folder_name}: {e}")
            raise

    def save_text_file(self, file_path: str, content: str) -> bool:
        try:
            if not isinstance(content, str):
                raise ValueError("Content must be a string")
            self.text_bytes(content)

            full_path = (self.base_dir / file_path).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid path")
            if full_path.exists() and full_path.is_dir():
                raise ValueError("Target is a directory")

            os.makedirs(full_path.parent, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(content)
            return True
        except Exception as e:
            PrintStyle.error(f"Error saving file {file_path}: {e}")
            raise

    def _is_allowed_file(self, filename: str, file) -> bool:
        # allow any file to be uploaded in file browser

        # if not filename:
        #     return False
        # ext = self._get_file_extension(filename)
        # all_allowed = set().union(*self.ALLOWED_EXTENSIONS.values())
        # if ext not in all_allowed:
        #     return False

        return True  # Allow the file if it passes the checks

    def _get_file_extension(self, filename: str) -> str:
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    def _get_files_via_ls(self, full_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get files and folders using ls command for better error handling"""
        files: List[Dict[str, Any]] = []
        folders: List[Dict[str, Any]] = []

        try:
            # Use ls command to get directory listing
            result = subprocess.run(
                ['ls', '-la', str(full_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                PrintStyle.error(f"ls command failed: {result.stderr}")
                return files, folders

            # Parse ls output (skip first line which is "total X")
            lines = result.stdout.strip().split('\n')
            if len(lines) <= 1:
                return files, folders

            for line in lines[1:]:  # Skip the "total" line
                try:
                    # Skip current and parent directory entries
                    if line.endswith(' .') or line.endswith(' ..'):
                        continue

                    # Parse ls -la output format
                    parts = line.split()
                    if len(parts) < 9:
                        continue

                    # Check if this is a symlink (permissions start with 'l')
                    permissions = parts[0]
                    is_symlink = permissions.startswith('l')

                    if is_symlink:
                        # For symlinks, extract the name before the '->' arrow
                        full_name_part = ' '.join(parts[8:])
                        if ' -> ' in full_name_part:
                            filename = full_name_part.split(' -> ')[0]
                            symlink_target = full_name_part.split(' -> ')[1]
                        else:
                            filename = full_name_part
                            symlink_target = None
                    else:
                        filename = ' '.join(parts[8:])  # Handle filenames with spaces
                        symlink_target = None

                    if not filename:
                        continue

                    # Get full path for this entry
                    entry_path = full_path / filename

                    try:
                        stat_info = entry_path.stat()

                        entry_data: Dict[str, Any] = {
                            "name": filename,
                            "path": str(entry_path.relative_to(self.base_dir)),
                            "modified": datetime.fromtimestamp(
                                stat_info.st_mtime,
                                tz=Localization.get().get_tzinfo(),
                            ).isoformat()
                        }

                        # Add symlink information if this is a symlink
                        if is_symlink and symlink_target:
                            entry_data["symlink_target"] = symlink_target
                            entry_data["is_symlink"] = True

                        if entry_path.is_file():
                            entry_data.update({
                                "type": self._get_file_type(filename),
                                "size": stat_info.st_size,
                                "is_dir": False
                            })
                            files.append(entry_data)
                        elif entry_path.is_dir():
                            entry_data.update({
                                "type": "folder",
                                "size": 0,  # Directories show as 0 bytes
                                "is_dir": True
                            })
                            folders.append(entry_data)

                    except (OSError, PermissionError, FileNotFoundError) as e:
                        # Log error but continue with other files
                        PrintStyle.warning(f"No access to {filename}: {e}")
                        continue

                    if len(files) + len(folders) > 10000:
                        break

                except Exception as e:
                    # Log error and continue with next line
                    PrintStyle.error(f"Error parsing ls line '{line}': {e}")
                    continue

        except subprocess.TimeoutExpired:
            PrintStyle.error("ls command timed out")
        except Exception as e:
            PrintStyle.error(f"Error running ls command: {e}")

        return files, folders

    def get_files(self, current_path: str = "") -> Dict:
        try:
            # Resolve the full path while preventing directory traversal
            full_path = (self.base_dir / current_path).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid path")
            if not full_path.exists():
                raise FileNotFoundError("Directory not found")
            if not full_path.is_dir():
                raise NotADirectoryError("Path is not a directory")

            # Use ls command instead of os.scandir for better error handling
            files, folders = self._get_files_via_ls(full_path)

            # Combine folders and files, folders first
            all_entries = folders + files

            # Get parent directory path if not at root
            parent_path = ""
            if current_path:
                try:
                    # Get the absolute path of current directory
                    current_abs = (self.base_dir / current_path).resolve()

                    # parent_path is empty only if we're already at root
                    if str(current_abs) != str(self.base_dir):
                        parent_path = str(Path(current_path).parent)

                except Exception:
                    parent_path = ""

            return {
                "entries": all_entries,
                "current_path": current_path,
                "parent_path": parent_path
            }

        except Exception as e:
            PrintStyle.error(f"Error reading directory: {e}")
            return {
                "entries": [],
                "current_path": current_path,
                "parent_path": "",
                "error": str(e),
            }

    def get_full_path(self, file_path: str, allow_dir: bool = False) -> str:
        """Get full file path if it exists and is within base_dir"""
        full_path = files.get_abs_path(self.base_dir, file_path)
        if not files.exists(full_path):
            raise ValueError(f"File {file_path} not found")
        return full_path

    def _get_file_type(self, filename: str) -> str:
        ext = self._get_file_extension(filename)
        for file_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return 'unknown'
