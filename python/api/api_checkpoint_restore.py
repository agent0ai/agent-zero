from agent import AgentContext
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.checkpoint_manager import CheckpointManager
from python.helpers.print_style import PrintStyle
from python.helpers import persist_chat
import json


class ApiCheckpointRestore(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Get checkpoint_id from input
            checkpoint_id = input.get("checkpoint_id")

            if not checkpoint_id:
                return Response(
                    '{"error": "checkpoint_id is required"}',
                    status=400,
                    mimetype="application/json"
                )

            # Load checkpoint
            manager = CheckpointManager.get()
            checkpoint = await manager.load_checkpoint(checkpoint_id)

            if not checkpoint:
                return Response(
                    '{"error": "Checkpoint not found"}',
                    status=404,
                    mimetype="application/json"
                )

            # Validate checkpoint
            validation = await manager.validate_checkpoint(checkpoint)
            if not validation.is_valid:
                return Response(
                    json.dumps({
                        "error": "Checkpoint validation failed",
                        "errors": validation.errors,
                        "warnings": validation.warnings
                    }),
                    status=400,
                    mimetype="application/json"
                )

            # Restore context from checkpoint
            restored_context = await manager.restore_context(checkpoint)

            # Save the restored context
            persist_chat.save_tmp_chat(restored_context)

            PrintStyle(
                background_color="#9B59B6", font_color="white", bold=True, padding=True
            ).print(f"API Checkpoint restored: {checkpoint_id} to context {checkpoint.context_id}")

            return {
                "success": True,
                "message": "Checkpoint restored successfully",
                "context_id": checkpoint.context_id,
                "checkpoint_id": checkpoint_id
            }

        except Exception as e:
            PrintStyle.error(f"API checkpoint restore error: {str(e)}")
            return Response(
                json.dumps({"error": f"Internal server error: {str(e)}"}),
                status=500,
                mimetype="application/json"
            )
