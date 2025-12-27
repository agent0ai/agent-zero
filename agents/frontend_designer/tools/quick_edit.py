from python.helpers.tool import Tool, Response
import os


class QuickEditTool(Tool):
    """Make targeted modifications to existing code files."""

    async def execute(self, **kwargs) -> Response:
        file_path = self.args.get("file_path", "")
        edits = self.args.get("edits", [])

        if not file_path:
            return Response(
                message="Error: file_path is required",
                break_loop=False
            )

        if not edits:
            return Response(
                message="Error: edits array is required",
                break_loop=False
            )

        try:
            # Read file
            if not os.path.exists(file_path):
                return Response(
                    message=f"Error: File not found: {file_path}",
                    break_loop=False
                )

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            applied_count = 0

            # Apply each edit
            for edit in edits:
                operation = edit.get("operation", "replace")

                if operation == "replace":
                    find = edit.get("find", "")
                    replace = edit.get("replace", "")

                    if find and find in content:
                        content = content.replace(find, replace)
                        applied_count += 1

                elif operation == "insert_after":
                    marker = edit.get("marker", "")
                    insert = edit.get("insert", "")

                    if marker and marker in content:
                        content = content.replace(marker, marker + insert)
                        applied_count += 1

                elif operation == "insert_before":
                    marker = edit.get("marker", "")
                    insert = edit.get("insert", "")

                    if marker and marker in content:
                        content = content.replace(marker, insert + marker)
                        applied_count += 1

            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                message = f"Successfully applied {applied_count} edit(s) to {file_path}\n\n"
                message += "File has been updated."
            else:
                message = f"No changes made to {file_path}\n\n"
                message += "None of the specified edits matched the file content."

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error editing file: {str(e)}",
                break_loop=False
            )
