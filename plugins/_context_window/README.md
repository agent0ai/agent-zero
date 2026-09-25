# Context Window

The bundled Context Window plugin adds a compact usage ring beside the chat's
model and agent selectors. Its popover shows token counts and full-window
percentages for Messages, System tools, Skills, MCP tools, System prompt,
Extras, and Free space.

Older chats gain the detailed breakdown after their next model turn. Mobile and
desktop visibility can be changed under **Settings > Interface**.

When a model provider reports usage, the popover shows price, cache-hit rate,
and input/output tokens. Unreported price and cache data are omitted. The
context breakdown does not guess model-specific image token costs.

For streamed chat calls, the transport requests LiteLLM's terminal usage
event and the plugin drains it after Agent Zero has accepted the response.
Price remains hidden when LiteLLM does not report a cost or map the selected
model.

Each finished model call also shows its output speed, such as `48.2 tok/s`, on
its generation step and in the popover. It counts the provider's output tokens
after the first one over the streaming time, so time to first token is not
included. Calls that stream for less than one second, paused calls, and calls
whose reasoning was not streamed show no speed. Hiding the Context Window
control in Interface settings hides the step labels too.
