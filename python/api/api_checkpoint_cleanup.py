from agent import AgentContext
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.checkpoint_manager import CheckpointManager
from python.helpers.print_style import PrintStyle
import json


class ApiCheckpointCleanup(ApiHandler):
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

            # Get checkpoint manager
            manager = CheckpointManager.get()

            # Get keep_last_n from context config or use default
            context = AgentContext.get(context_id)
            if context:
                keep_last_n = getattr(context.config, 'checkpoint_keep_last_n', 5)
            else:
                # Context doesn't exist (deleted chat), use default
                keep_last_n = 5

            # Cleanup old checkpoints (works even if context is deleted)
            deleted_count = await manager.cleanup_checkpoints(context_id, keep_last_n)

            PrintStyle(
                background_color="#F39C12", font_color="white", bold=True, padding=True
            ).print(f"API Checkpoint cleanup: {deleted_count} old checkpoints removed for context {context_id}")

            return {
                "success": True,
                "message": f"Cleaned up {deleted_count} old checkpoints",
                "deleted": deleted_count
            }

        except Exception as e:
            PrintStyle.error(f"API checkpoint cleanup error: {str(e)}")
            return Response(
                json.dumps({"error": f"Internal server error: {str(e)}"}),
                status=500,
                mimetype="application/json"
            )
