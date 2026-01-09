from python.helpers.api import ApiHandler, Request, Response

class Nudge(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")

        context = self.use_context(ctxid)
        agent = context.get_agent()
        context.nudge()

        msg = f"Agent {agent.number} nudged."
        context.log.log(type="info", content=msg)

        return {
            "message": msg,
            "ctxid": context.id,
            "agent_number": agent.number,
        }