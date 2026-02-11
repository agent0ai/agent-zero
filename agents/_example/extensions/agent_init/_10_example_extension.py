from python.helpers.extension import Extension

# this is an example extension that renames the current agent when initialized
# see /extensions folder for all available extension points


class ExampleExtension(Extension):
    async def execute(self, **kwargs):
        # rename the agent to SuperApollos
        self.agent.agent_name = "SuperApollos" + str(self.agent.number)
