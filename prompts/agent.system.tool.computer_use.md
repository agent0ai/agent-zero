### computer_use

granular browser control with individual actions
use for precise web automation tasks when browser_agent is too high-level
available methods: navigate, click, type, scroll, observe_page, select, press, hover, pause_for_user, get_browser_info
screenshots captured automatically after each action for visual feedback

**navigate** - go to URL
**click** - click element by CSS selector or text
**type** - type text into input field
**scroll** - scroll page (direction: up/down/left/right)
**observe_page** - get current page state, title, content, elements (adds screenshot to context)
**select** - select option from dropdown
**press** - press keyboard key on element
**hover** - hover over element
**pause_for_user** - pause execution for manual user interaction (CAPTCHAs, manual login, etc.)
  - requires browser to be in visible mode (headless=False)
  - waits specified seconds for user to interact with browser
  - use when encountering CAPTCHAs, blocked automation, or manual verification needed
**get_browser_info** - diagnostic tool to check browser visibility mode and troubleshoot
  - shows current headless/visible mode
  - displays configuration settings
  - provides troubleshooting tips if browser not visible
  - use when you can't see the browser window or need to verify settings

session management:
- browser state persists across calls
- use reset arg to start fresh session
- same page context maintained between actions
- screenshots available in chat history

usage examples:

1. Navigate and observe
~~~json
{
    "thoughts": ["Need to open the website and see what's there"],
    "headline": "Opening website",
    "tool_name": "computer_use:navigate",
    "tool_args": {
        "url": "https://example.com"
    }
}
~~~

2. Observe current page
~~~json
{
    "thoughts": ["Let me see what's on this page"],
    "headline": "Observing page content",
    "tool_name": "computer_use:observe_page",
    "tool_args": {}
}
~~~

3. Click element
~~~json
{
    "thoughts": ["Need to click the login button"],
    "headline": "Clicking login button",
    "tool_name": "computer_use:click",
    "tool_args": {
        "selector": "button[type='submit']"
    }
}
~~~

4. Type into field
~~~json
{
    "thoughts": ["Entering username"],
    "headline": "Typing username",
    "tool_name": "computer_use:type",
    "tool_args": {
        "selector": "input[name='username']",
        "text": "myusername"
    }
}
~~~

5. Scroll page
~~~json
{
    "thoughts": ["Need to see more content"],
    "headline": "Scrolling down",
    "tool_name": "computer_use:scroll",
    "tool_args": {
        "direction": "down"
    }
}
~~~

6. Select dropdown option
~~~json
{
    "thoughts": ["Need to select country from dropdown"],
    "headline": "Selecting country",
    "tool_name": "computer_use:select",
    "tool_args": {
        "selector": "select[name='country']",
        "value": "USA"
    }
}
~~~

7. Press key
~~~json
{
    "thoughts": ["Need to submit form with Enter key"],
    "headline": "Pressing Enter",
    "tool_name": "computer_use:press",
    "tool_args": {
        "selector": "input[name='search']",
        "key": "Enter"
    }
}
~~~

8. Hover over element
~~~json
{
    "thoughts": ["Need to hover over menu to reveal submenu"],
    "headline": "Hovering over menu",
    "tool_name": "computer_use:hover",
    "tool_args": {
        "selector": "#main-menu"
    }
}
~~~

9. Pause for user interaction
~~~json
{
    "thoughts": ["Encountered a CAPTCHA that needs manual solving"],
    "headline": "Pausing for CAPTCHA",
    "tool_name": "computer_use:pause_for_user",
    "tool_args": {
        "wait_seconds": 120,
        "message": "Please solve the CAPTCHA"
    }
}
~~~

10. Check browser visibility and settings
~~~json
{
    "thoughts": ["User says they can't see the browser window, let me check the configuration"],
    "headline": "Checking browser settings",
    "tool_name": "computer_use:get_browser_info",
    "tool_args": {}
}
~~~

11. Reset session
~~~json
{
    "thoughts": ["Browser session seems stuck, starting fresh"],
    "headline": "Resetting browser session",
    "tool_name": "computer_use:navigate",
    "tool_args": {
        "url": "https://example.com",
        "reset": "true"
    }
}
~~~

**configuration:**
- to enable visible browser for manual interaction: set `computer_use_headless: False` in agent config
- default is headless mode (browser runs invisibly in background)
- visible mode required for pause_for_user to work
- start URL can be configured with `computer_use_start_url`
- timeout can be configured with `computer_use_timeout` (milliseconds)

**best practices:**
- always observe_page first to understand current state
- use specific CSS selectors when possible (id, class, name attribute)
- for text-based clicking, selector will be treated as text content
- handle failures gracefully - try alternative selectors if needed
- reset session if browser gets stuck or navigation fails repeatedly
- each action is atomic - chain multiple actions for complex workflows
- screenshots show visual state after each action
- observe_page adds screenshot to your context for vision analysis
- use pause_for_user when encountering CAPTCHAs or automation blocks
- use get_browser_info when user reports browser visibility issues
- if browser was initialized in wrong mode, use reset=true to restart it

