import json
from agent import LoopData
from helpers.extension import Extension


class InitialMessage(Extension):

    def execute(self, **kwargs):
        """
        Add an initial greeting message when first user message is processed.
        Called only once per session via _process_chain method.
        """
        if not self.agent:
            return

        # Only add initial message for main agent (A0), not subordinate agents
        if self.agent.number != 0:
            return

        # If the context already contains log messages, do not add another initial message
        if self.agent.context.log.logs:
            return

        # Construct the initial message from prompt template
        initial_message = self.agent.read_prompt("fw.initial_message.md")

        # add initial loop data to agent (for hist_add_ai_response)
        self.agent.loop_data = LoopData(user_message=None)

        # Add the message to history as an AI response
        msg = self.agent.hist_add_ai_response(initial_message)

        # json parse the message, get the tool_args text
        initial_message_json = json.loads(initial_message)
        initial_message_text = initial_message_json.get("tool_args", {}).get("text", "Hello! How can I help you?")

        # Add to log (green bubble) for immediate UI display
        self.agent.context.log.log(
            type="response",
            content=initial_message_text,
            finished=True,
            update_progress="none",
            id=msg.id,
        )
