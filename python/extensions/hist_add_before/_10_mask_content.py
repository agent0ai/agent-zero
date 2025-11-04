from python.helpers.extension import Extension


class MaskHistoryContent(Extension):

    async def execute(self, **kwargs):
        # Get content data from kwargs
        content_data = kwargs.get("content_data")
        if not content_data:
            return

        try:
            from python.helpers.secrets import SecretsManager
            secrets_mgr = SecretsManager.get_instance()

            # Mask the content before adding to history
            content_data["content"] = self._mask_content(content_data["content"], secrets_mgr)
        except Exception as e:
            # If masking fails, proceed without masking
            pass

    def _mask_content(self, content, secrets_mgr):
        """Recursively mask secrets in message content."""
        if isinstance(content, str):
            return secrets_mgr.mask_values(content)
        elif isinstance(content, list):
            return [self._mask_content(item, secrets_mgr) for item in content]
        elif isinstance(content, dict):
            return {k: self._mask_content(v, secrets_mgr) for k, v in content.items()}
        else:
            # For other types, return as-is
            return content
