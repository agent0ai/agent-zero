from agent import AgentContext
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.checkpoint_manager import CheckpointManager
from python.helpers.print_style import PrintStyle
import json


class ApiCheckpointCreate(ApiHandler):
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
            # Get context_id from input
            context_id = input.get("context_id")

            if not context_id:
                return Response(
                    '{"error": "context_id is required"}',
                    status=400,
                    mimetype="application/json"
                )

            # Check if context exists and use it
            context = self.use_context(context_id, create_if_not_exists=False)
            if not context:
                return Response(
                    '{"error": "Chat context not found"}',
                    status=404,
                    mimetype="application/json"
                )

            # Create checkpoint
            manager = CheckpointManager.get()
            checkpoint = await manager.create_checkpoint(context, checkpoint_type="manual")
            await manager.save_checkpoint(checkpoint)

            PrintStyle(
                background_color="#2ECC71", font_color="white", bold=True, padding=True
            ).print(f"API Checkpoint created: {checkpoint.checkpoint_id} for context {context_id}")

            return {
                "success": True,
                "message": "Checkpoint created successfully",
                "checkpoint_id": checkpoint.checkpoint_id,
                "created_at": checkpoint.created_at.isoformat()
            }

        except Exception as e:
            PrintStyle.error(f"API checkpoint create error: {str(e)}")
            return Response(
                json.dumps({"error": f"Internal server error: {str(e)}"}),
                status=500,
                mimetype="application/json"
            )
