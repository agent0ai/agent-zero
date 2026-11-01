import json
import logging
import os

from helpers.api import ApiHandler, Request, Response, send_file
from helpers.backup import BackupService
from helpers.backup_jobs import backup_jobs
from helpers.persist_chat import save_tmp_chats

logger = logging.getLogger(__name__)


class BackupCreate(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_loopback(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            action = input.get("action")
            if action == "status":
                return backup_jobs.status(input.get("job_id", ""))
            if action == "download":
                job_id = input.get("job_id", "")
                stream, name, sha256 = backup_jobs.acquire_download(job_id)
                try:
                    response = send_file(
                        stream,
                        as_attachment=True,
                        download_name=name,
                        mimetype="application/zip",
                    )
                    response.content_length = os.fstat(stream.fileno()).st_size
                    response.headers["X-Content-SHA256"] = sha256
                    # Ensure WSGI closes the response and releases the archive lease.
                    response.direct_passthrough = False
                    response.call_on_close(
                        lambda: backup_jobs.release_download(job_id, stream)
                    )
                    return response
                except Exception:
                    backup_jobs.release_download(job_id, stream)
                    raise
            if action not in (None, "start"):
                raise ValueError("Unknown backup action")

            # Get input parameters
            include_patterns = input.get("include_patterns", [])
            exclude_patterns = input.get("exclude_patterns", [])
            include_hidden = input.get("include_hidden", True)
            backup_name = input.get("backup_name", "agent-zero-backup")

            # Support legacy string patterns format for backward compatibility
            patterns_string = input.get("patterns", "")
            if patterns_string and not include_patterns and not exclude_patterns:
                # Parse legacy format
                lines = [
                    line.strip()
                    for line in patterns_string.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                for line in lines:
                    if line.startswith("!"):
                        exclude_patterns.append(line[1:])
                    else:
                        include_patterns.append(line)

            if action == "start":
                if (
                    not isinstance(backup_name, str)
                    or not backup_name.strip()
                    or any(char in backup_name for char in "\r\n")
                ):
                    raise ValueError(
                        "backup_name must be a non-empty single-line string"
                    )

                async def create_archive(output_path: str) -> None:
                    save_tmp_chats()
                    await BackupService().create_backup(
                        include_patterns=include_patterns,
                        exclude_patterns=exclude_patterns,
                        include_hidden=include_hidden,
                        backup_name=backup_name,
                        output_path=output_path,
                    )

                return backup_jobs.start(backup_name, create_archive)

            # Save all chats to the chats folder
            save_tmp_chats()

            # Create backup service and generate backup
            backup_service = BackupService()
            zip_path = await backup_service.create_backup(
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                include_hidden=include_hidden,
                backup_name=backup_name,
            )

            # Return file for download
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"{backup_name}.zip",
                mimetype="application/zip",
            )

        except Exception as e:
            if input.get("action") is not None:
                if isinstance(e, KeyError):
                    message, status = e.args[0], 404
                elif isinstance(e, RuntimeError):
                    message, status = str(e), 409
                elif isinstance(e, ValueError):
                    message, status = str(e), 400
                else:
                    logger.exception("Backup request failed")
                    message, status = (
                        "Backup request failed. See the server log for details.",
                        500,
                    )
                return Response(
                    json.dumps(
                        {
                            "success": False,
                            "error": message,
                            "code": "backup_not_found"
                            if status == 404
                            else "backup_request_failed",
                        }
                    ),
                    status=status,
                    mimetype="application/json",
                )
            return {"success": False, "error": str(e)}
