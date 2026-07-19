# Creating Discovery Cards and Banners

Agent Zero allows plugin developers to surface UI elements using the `banners` extension point. This allows your plugin to present information, prompts, or actionable "discovery cards" directly on the Welcome Screen without needing to inject arbitrary HTML into the frontend.

## The `banners` Extension Point

Banners are collected on the backend and sent to the frontend UI as an array of dictionaries. By appending to the `banners` array inside a Python extension, you can easily surface your plugin to the user.

To inject a banner, you create a Python extension script hooking into `banners`.

### Where to put your extension script

Create a python file in your plugin's extensions folder:
`plugins/<your_plugin>/extensions/python/banners/10_my_plugin_banner.py`

*(Note: the `10_` prefix is for ordering; extensions run in alphabetical order).*

## Banner Types

The UI distinguishes banners primarily by the `type` property.

### 1. Alert Banners (`info`, `warning`, `error`)
These are standard top-level alerts displayed on the welcome screen.

```python
banners.append({
    "id": "my-plugin-warning",
    "type": "warning",
    "priority": 90,
    "title": "My Plugin Issue",
    "html": "<strong>Action required:</strong> Please configure your settings.",
    "dismissible": True,
})
```

### 2. Discovery Cards (`hero`, `feature`)
These are rich, interactive cards displayed in the Discovery section. They are designed to prompt the user to try new plugins or features.

*   `hero`: A wide, prominent card. Usually reserved for core system features (e.g., the Plugin Hub).
*   `feature`: A smaller card in a grid layout. This is the **recommended type** for plugin contributors to showcase their plugin.

### Anatomy of a Discovery Card

Here is an example of injecting a `feature` card for a custom plugin:

```python
from helpers.extension import Extension
from helpers import plugins

class MyPluginDiscoveryCard(Extension):
    """Injects a discovery card for My Custom Plugin."""

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        # 1. Condition Check
        # Only show the discovery card if the user hasn't configured the plugin yet.
        config = plugins.get_plugin_config("my_custom_plugin") or {}
        
        # If the API key is already set, we don't need to advertise the setup!
        if config.get("api_key"):
            return

        # 2. Add the Card
        banners.append({
            "id": "discovery-my-custom-plugin",
            "type": "feature",                     # 'feature' or 'hero'
            "title": "Connect My Service",         # Card title
            "description": "Unlock amazing capabilities by linking your account.",
            
            # Visuals (use either thumbnail OR icon)
            "thumbnail": "/plugins/my_custom_plugin/assets/thumb.png", # Path to image
            "icon": "bolt",                        # Or a Material Symbol icon name
            
            # Call To Action (CTA)
            "cta_text": "Setup Now",
            "cta_action": "open-plugin-config:my_custom_plugin", # Opens your plugin's config modal
            
            # Behavior
            "dismissible": True,                   # Let the user hide it
            "priority": 40,                        # Higher numbers appear first
        })
```

## Call To Action (CTA) Actions

When a user clicks the button on a discovery card, the `cta_action` string determines what happens. The frontend currently supports the following actions:

*   `open-plugin-config:<plugin_folder_name>`: Automatically opens the settings modal for the specified plugin. (e.g., `open-plugin-config:_telegram_integration`).
*   `open-plugin-hub`: Opens the main Plugin Hub UI.
*   `open-url:<url>`: Opens a web link in a new browser tab. (e.g., `open-url:https://example.com/docs`).

## Best Practices

1.  **Check Configuration First**: Always check your plugin's configuration before injecting a card. If the user has already set up your plugin, they shouldn't keep seeing a discovery card asking them to set it up.
2.  **Unique IDs**: Ensure your banner `id` is highly unique (e.g., prefix it with your plugin name) to avoid collisions with other plugins.
3.  **Use `feature` type**: Community plugins should stick to the `feature` type rather than `hero` to ensure a clean grid layout for users.