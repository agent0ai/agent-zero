from python.helpers.api import ApiHandler, Request, Response
from python.helpers.checkpoint_manager import CheckpointManager
from python.helpers.print_style import PrintStyle
import json


class ApiCheckpointDelete(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["DELETE"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Get checkpoint_id from input (for DELETE requests, we use JSON body)
            checkpoint_id = input.get("checkpoint_id")

            if not checkpoint_id:
                return Response(
                    '{"error": "checkpoint_id is required"}',
                    status=400,
                    mimetype="application/json"
                )

            # Delete checkpoint
            manager = CheckpointManager.get()
            success = await manager.delete_checkpoint(checkpoint_id)

            if not success:
                return Response(
                    '{"error": "Checkpoint not found"}',
                    status=404,
                    mimetype="application/json"
                )

            PrintStyle(
                background_color="#E74C3C", font_color="white", bold=True, padding=True
            ).print(f"API Checkpoint deleted: {checkpoint_id}")

            return {
                "success": True,
                "message": "Checkpoint deleted successfully",
                "checkpoint_id": checkpoint_id
            }

        except Exception as e:
            PrintStyle.error(f"API checkpoint delete error: {str(e)}")
            return Response(
                json.dumps({"error": f"Internal server error: {str(e)}"}),
                status=500,
                mimetype="application/json"
            )
