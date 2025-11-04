from typing import Any
from python.helpers.extension import Extension
from python.helpers import files, persist_chat
import os, re

LEN_MIN = 500

class SaveToolCallFile(Extension):
    async def execute(self, data: dict[str, Any] | None = None, **kwargs):
        if not data:
            return

        # get tool call result
        result = data.get("tool_result") if isinstance(data, dict) else None
        if result is None:
            return

        # skip short results
        if len(str(result)) < LEN_MIN:
            return

        # message files directory
        msgs_folder = persist_chat.get_chat_msg_files_folder(self.agent.context.id)
        os.makedirs(msgs_folder, exist_ok=True)

        # count the files in the directory
        last_num = len(os.listdir(msgs_folder))

        # create new file
        new_file = files.get_abs_path(msgs_folder, f"{last_num+1}.txt")
        files.write_file(
            new_file,
            result,
        )

        # add the path to the history
        data["file"] = new_file
