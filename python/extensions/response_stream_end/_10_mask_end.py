from python.helpers.extension import Extension
from python.helpers.secrets import SecretsManager


class MaskResponseStreamEnd(Extension):
    async def execute(self, **kwargs):
        # Get agent and finalize the streaming filter
        agent = kwargs.get("agent")
        if not agent:
            return

        try:
            # Finalize the response stream filter if it exists
            filter_key = "_resp_stream_filter"
            filter_instance = agent.get_data(filter_key)
            if filter_instance:
                tail = filter_instance.finalize()

                # Print any remaining masked content
                if tail:
                    from python.helpers.print_style import PrintStyle
                    PrintStyle().stream(tail)

                # Clean up the filter
                agent.set_data(filter_key, None)
        except Exception as e:
            # If masking fails, proceed without masking
            pass
