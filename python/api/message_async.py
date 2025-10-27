from agent import AgentContext
from python.helpers.defer import DeferredTask
from python.api.message import Message


class MessageAsync(Message):
    async def respond(self, task: DeferredTask, context: AgentContext):
        # Return immediately - the task processes in the background
        return {
            "message": "Message received.",
            "context": context.id,
        }
