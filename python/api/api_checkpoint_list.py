from agent import AgentContext
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.checkpoint_manager import CheckpointManager
from python.helpers.print_style import PrintStyle
import json


class ApiCheckpointList(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Get context_id from query parameters (optional)
            context_id = request.args.get("context_id")
            show_all = request.args.get("all", "false").lower() == "true"

            # Get checkpoint manager
            manager = CheckpointManager.get()

            # If showing all checkpoints across all contexts
            if show_all or not context_id:
                all_checkpoints_metadata = await manager.list_checkpoints(context_id=None)

                # Get all active contexts
                active_contexts = {ctx.id: ctx for ctx in AgentContext.all()}

                # Group checkpoints by context
                checkpoints_by_context = {}
                for cp in all_checkpoints_metadata:
                    if cp.context_id not in checkpoints_by_context:
                        ctx = active_contexts.get(cp.context_id)
                        checkpoints_by_context[cp.context_id] = {
                            "context_id": cp.context_id,
                            "context_name": ctx.name if ctx else "Closed Chat",
                            "is_active": ctx is not None,
                            "checkpoints": []
                        }

                    checkpoints_by_context[cp.context_id]["checkpoints"].append({
                        "checkpoint_id": cp.checkpoint_id,
                        "created_at": cp.created_at.isoformat(),
                        "checkpoint_type": cp.checkpoint_type,
                        "message_count": cp.message_count,
                        "tool_execution_count": cp.tool_execution_count,
                    })

                # Convert to list and sort
                contexts_list = list(checkpoints_by_context.values())
                for ctx_data in contexts_list:
                    ctx_data["checkpoints"].sort(key=lambda cp: cp["created_at"], reverse=True)
                contexts_list.sort(
                    key=lambda ctx: ctx["checkpoints"][0]["created_at"] if ctx["checkpoints"] else "",
                    reverse=True
                )

                PrintStyle(
                    background_color="#3498DB", font_color="white", bold=True, padding=True
                ).print(f"API Checkpoint list all: {len(contexts_list)} contexts with checkpoints")

                return {
                    "success": True,
                    "contexts": contexts_list,
                    "total_checkpoints": len(all_checkpoints_metadata)
                }

            # Single context mode
            else:
                # Check if context exists
                context = AgentContext.use(context_id)
                if not context:
                    return Response(
                        '{"error": "Chat context not found"}',
                        status=404,
                        mimetype="application/json"
                    )

                checkpoints_metadata = await manager.list_checkpoints(context_id)

                # Convert to serializable format
                checkpoints = [
                    {
                        "checkpoint_id": cp.checkpoint_id,
                        "context_id": cp.context_id,
                        "created_at": cp.created_at.isoformat(),
                        "checkpoint_type": cp.checkpoint_type,
                        "message_count": cp.message_count,
                        "tool_execution_count": cp.tool_execution_count,
                    }
                    for cp in checkpoints_metadata
                ]

                PrintStyle(
                    background_color="#3498DB", font_color="white", bold=True, padding=True
                ).print(f"API Checkpoint list: {context_id} ({len(checkpoints)} checkpoints)")

                return {
                    "success": True,
                    "checkpoints": checkpoints
                }

        except Exception as e:
            PrintStyle.error(f"API checkpoint list error: {str(e)}")
            return Response(
                json.dumps({"error": f"Internal server error: {str(e)}"}),
                status=500,
                mimetype="application/json"
            )
