from python.helpers.extension import Extension


class MaskReasoningStreamChunk(Extension):
    async def execute(self, **kwargs):
        # Get stream data and agent from kwargs
        stream_data = kwargs.get("stream_data")
        agent = kwargs.get("agent")
        if not agent or not stream_data:
            return

        try:
            from python.helpers.secrets import SecretsManager
            secrets_mgr = SecretsManager.get_instance()

            # Initialize filter if not exists
            filter_key = "_reason_stream_filter"
            filter_instance = agent.get_data(filter_key)
            if not filter_instance:
                filter_instance = secrets_mgr.create_streaming_filter()
                agent.set_data(filter_key, filter_instance)

            # Process the chunk through the streaming filter
            processed_chunk = filter_instance.process_chunk(stream_data["chunk"])

            # Update the stream data with processed chunk
            stream_data["chunk"] = processed_chunk

            # Also mask the full text for consistency
            stream_data["full"] = secrets_mgr.mask_values(stream_data["full"])

            # Print the processed chunk (this is where printing should happen)
            if processed_chunk:
                from python.helpers.print_style import PrintStyle
                PrintStyle().stream(processed_chunk)
        except Exception as e:
            # If masking fails, proceed without masking
            pass
