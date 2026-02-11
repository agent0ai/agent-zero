import asyncio
import re
import traceback
from typing import Literal


def handle_error(e: Exception):
    # if asyncio.CancelledError, re-raise
    if isinstance(e, asyncio.CancelledError):
        raise e


def error_text(e: Exception):
    return str(e)


def format_error(
    e: Exception,
    start_entries=20,
    end_entries=15,
    error_message_position: Literal["top", "bottom", "none"] = "top",
):
    # format traceback from the provided exception instead of the most recent one
    traceback_text = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    # Split the traceback into lines
    lines = traceback_text.split("\n")

    if not start_entries and not end_entries:
        trimmed_lines = []
    else:
        # Find all "File" lines
        file_indices = [
            i for i, line in enumerate(lines) if line.strip().startswith("File ")
        ]

        # If we found at least one "File" line, trim the middle if there are more than start_entries+end_entries lines
        if len(file_indices) > start_entries + end_entries:
            start_index = max(0, len(file_indices) - start_entries - end_entries)
            trimmed_lines = (
                lines[: file_indices[start_index]]
                + [
                    f"\n>>>  {len(file_indices) - start_entries - end_entries} stack lines skipped <<<\n"
                ]
                + lines[file_indices[start_index + end_entries] :]
            )
        else:
            # If no "File" lines found, or not enough to trim, just return the original traceback
            trimmed_lines = lines

    # Find the error message at the end
    error_message = ""
    for line in reversed(lines):
        # match both simple errors and module.path.Error patterns
        if re.match(r"[\w\.]+Error:\s*", line):
            error_message = line
            break

    if error_message and error_message_position in ("top", "bottom", "none"):
        for i in range(len(trimmed_lines) - 1, -1, -1):
            if trimmed_lines[i].strip() == error_message.strip():
                trimmed_lines = trimmed_lines[:i] + trimmed_lines[i + 1 :]
                break

    # Combine the trimmed traceback with the error message
    if not trimmed_lines:
        result = "" if error_message_position == "none" else error_message
    else:
        result = "Traceback (most recent call last):\n" + "\n".join(trimmed_lines)

    if error_message and error_message_position == "top":
        result = f"{error_message}\n\n{result}" if result else error_message
    elif error_message and error_message_position == "bottom":
        result = f"{result}\n\n{error_message}" if result else error_message

    # at least something
    if not result:
        result = str(e)

    return result


class RepairableException(Exception):
    """An exception type indicating errors that can be surfaced to the LLM for potential self-repair."""

    pass
