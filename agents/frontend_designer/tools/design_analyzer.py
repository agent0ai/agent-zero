import base64
from python.helpers.tool import Tool, Response
from python.helpers import files, images, runtime
from mimetypes import guess_type
from langchain_core.messages import HumanMessage


class DesignAnalyzerTool(Tool):
    """Analyze screenshots and design mockups to extract design specifications."""

    async def execute(self, **kwargs) -> Response:
        image_path = self.args.get("image_path", "")

        if not image_path:
            return Response(
                message="Error: image_path is required",
                break_loop=False
            )

        # Check if file exists
        if not await runtime.call_development_function(files.exists, str(image_path)):
            return Response(
                message=f"Error: Image file not found: {image_path}",
                break_loop=False
            )

        # Check if file is an image
        mime_type, _ = guess_type(str(image_path))
        if not mime_type or not mime_type.startswith("image/"):
            return Response(
                message=f"Error: File is not a supported image format: {image_path}",
                break_loop=False
            )

        try:
            # Load and compress image
            file_content = await runtime.call_development_function(
                files.read_file_base64, str(image_path)
            )
            file_content = base64.b64decode(file_content)

            # Compress image (max 768k pixels, 75% quality like vision_load)
            compressed = images.compress_image(
                file_content, max_pixels=768_000, quality=75
            )

            # Encode as base64
            image_b64 = base64.b64encode(compressed).decode("utf-8")

            # Load design analysis prompt from prompts folder
            analysis_prompt = self.agent.read_prompt("design_analysis.system.md")

            # Call the agent's chat model with vision capabilities
            vision_message = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ]
                )
            ]

            # Use the agent's chat model to analyze the image
            response_text, _reasoning = await self.agent.call_chat_model(
                messages=vision_message,
                response_callback=None,
                reasoning_callback=None,
            )

            # Format the response
            message = f"# Design Analysis: {image_path}\n\n"
            message += response_text
            message += "\n\n---\n"
            message += "*Analysis generated using vision model integration*"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error analyzing design: {str(e)}",
                break_loop=False
            )
