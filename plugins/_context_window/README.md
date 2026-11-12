# Context Window

The bundled Context Window plugin adds a compact usage ring beside the chat's
model and agent selectors. Its popover shows token counts and full-window
percentages for Messages, System tools, Skills, MCP tools, System prompt,
Extras, and Free space.

Older chats gain the detailed breakdown after their next model turn. Mobile and
desktop visibility can be changed under **Settings > Interface**.

Under **Plugins > Context Window > Settings**, show or hide the whole breakdown
block, Price, Cache hit, and Tokens In/Out independently. All four are visible
by default. These global settings apply when the popover next refreshes or opens.

**Price currency** defaults to USD and uses the provider's reported amount
directly, with no exchange-rate request. Other currencies convert the visible
price using [Frankfurter's daily reference rates](https://frankfurter.dev/).
Rates are cached for 24 hours; no chat content or prices are sent to the rate
service. Hover over a converted amount to see the rate date. If a rate is
unavailable, the price is explicitly shown in USD and retries wait five minutes.

When a model provider reports usage, the popover shows price, cache-hit rate,
and input/output tokens. Unreported price and cache data are omitted. The
context breakdown does not guess model-specific image token costs.

For streamed chat calls, the transport requests LiteLLM's terminal usage
event and the plugin drains it after Agent Zero has accepted the response.
Price remains hidden when LiteLLM does not report a cost or map the selected
model.
