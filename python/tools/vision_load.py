import base64
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Tool, Response
from python.helpers import runtime, files, images
from mimetypes import guess_type
from python.helpers import history

# image optimization and token estimation for context window
MAX_PIXELS = 768_000
QUALITY = 75
TOKENS_ESTIMATE = 1500


class VisionLoad(Tool):
    async def execute(self, paths: list[str] = [], **kwargs) -> Response:

        self.images_dict = {}
        self.image_descriptions = {}
        template: list[dict[str, str]] = []  # type: ignore
        
        # Get vision strategy from settings
        from python.helpers.settings import get_settings
        settings = get_settings()
        vision_strategy = settings.get("chat_vision_strategy", "native")

        for path in paths:
            if not await runtime.call_development_function(files.exists, str(path)):
                continue

            if path not in self.images_dict:
                mime_type, _ = guess_type(str(path))
                if mime_type and mime_type.startswith("image/"):
                    try:
                        # Read binary file
                        file_content = await runtime.call_development_function(
                            files.read_file_base64, str(path)
                        )
                        file_content = base64.b64decode(file_content)
                        # Compress and convert to JPEG
                        compressed = images.compress_image(
                            file_content, max_pixels=MAX_PIXELS, quality=QUALITY
                        )
                        # Encode as base64
                        file_content_b64 = base64.b64encode(compressed).decode("utf-8")

                        # DEBUG: Save compressed image
                        # await runtime.call_development_function(
                        #     files.write_file_base64, str(path), file_content_b64
                        # )

                        # Construct the data URL (always JPEG after compression)
                        self.images_dict[path] = file_content_b64
                    except Exception as e:
                        self.images_dict[path] = None
                        PrintStyle().error(f"Error processing image {path}: {e}")
                        self.agent.context.log.log("warning", f"Error processing image {path}: {e}")

        return Response(message="dummy", break_loop=False)

    async def after_execution(self, response: Response, **kwargs):
        from python.helpers.settings import get_settings
        from langchain_core.messages import HumanMessage
        
        settings = get_settings()
        vision_strategy = settings.get("chat_vision_strategy", "native")
        
        # Check if vision is enabled via "Supports Vision" switch
        vision_enabled = self.agent.config.chat_model.vision
        
        # If vision is disabled, skip all processing
        if not vision_enabled:
            self.agent.hist_add_tool_result(self.name, "Vision is not enabled for chat model")
            PrintStyle(font_color="#85C1E9").print("Vision not enabled")
            self.log.update(result="Vision not enabled")
            return

        # Handle dedicated strategy
        if vision_strategy == "dedicated" and self.images_dict:
            descriptions = []
            for path, image in self.images_dict.items():
                if image:
                    try:
                        # Send image to vision model for analysis
                        vision_model = self.agent.get_vision_model()
                        
                        # Create message with image for vision model
                        vision_content = [
                            {
                                "type": "text",
                                "text": "Describe this image in detail. Focus on all visible elements, text, colors, layout, and any important information."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                            }
                        ]
                        
                        vision_message = HumanMessage(content=vision_content)
                        
                        # Call vision model
                        description, _ = await vision_model.unified_call(
                            messages=[vision_message],
                            rate_limiter_callback=self.agent.rate_limiter_callback
                        )
                        
                        descriptions.append(f"Image: {path}\n{description}")
                        
                    except Exception as e:
                        error_msg = f"Error analyzing image {path} with vision model: {e}"
                        PrintStyle().error(error_msg)
                        descriptions.append(f"Image: {path}\nError: {error_msg}")
            
            # Add text descriptions to history instead of raw images
            if descriptions:
                combined_description = "\n\n---\n\n".join(descriptions)
                self.agent.hist_add_tool_result(
                    self.name, 
                    f"Image Analysis (via dedicated vision model):\n\n{combined_description}"
                )
                message = f"{len(descriptions)} images analyzed by vision model"
            else:
                self.agent.hist_add_tool_result(self.name, "No images analyzed")
                message = "No images analyzed"
                
            PrintStyle(
                font_color="#1B4F72", background_color="white", padding=True, bold=True
            ).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
            PrintStyle(font_color="#85C1E9").print(message)
            self.log.update(result=message)
            return

        # Handle native strategy (original behavior)
        content = []
        if self.images_dict:
            for path, image in self.images_dict.items():
                if image:
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                        }
                    )
                else:
                    content.append(
                        {
                            "type": "text",
                            "text": "Error processing image " + path,
                        }
                    )
            # append as raw message content for LLMs with vision tokens estimate
            msg = history.RawMessage(raw_content=content, preview="<Base64 encoded image data>")
            self.agent.hist_add_message(
                False, content=msg, tokens=TOKENS_ESTIMATE * len(content)
            )
        else:
            self.agent.hist_add_tool_result(self.name, "No images processed")

        # print and log short version
        message = (
            "No images processed"
            if not self.images_dict
            else f"{len(self.images_dict)} images processed"
        )
        PrintStyle(
            font_color="#1B4F72", background_color="white", padding=True, bold=True
        ).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color="#85C1E9").print(message)
        self.log.update(result=message)
