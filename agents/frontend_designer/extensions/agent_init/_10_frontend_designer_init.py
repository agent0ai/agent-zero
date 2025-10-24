from python.helpers.extension import Extension


class FrontendDesignerExtension(Extension):
    """Initialize frontend designer agent configuration."""

    async def execute(self, **kwargs):
        # Set agent name
        self.agent.agent_name = "FE Designer " + str(self.agent.number)

        # Initialize frontend-specific state
        if not hasattr(self.agent.context, 'state'):
            self.agent.context.state = {}

        # Set default preferences
        self.agent.context.state['styling_framework'] = 'tailwind'
        self.agent.context.state['component_library'] = 'shadcn-ui'
        self.agent.context.state['typescript_enabled'] = True
        self.agent.context.state['accessibility_level'] = 'AA'

        # Log initialization
        from python.helpers.print_style import PrintStyle
        PrintStyle(
            font_color="#10B981",
            background_color="white",
            padding=True,
            bold=True
        ).print(f"Frontend Designer Agent Initialized: {self.agent.agent_name}")
