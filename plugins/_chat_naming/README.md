# Chat Naming

Chat Naming adds a standard sidebar action for manually renaming chats and tasks. Its modal can ask the chat's configured Utility Model to suggest a concise name from recent user messages.

Automatic naming is configured per project and agent profile. By default, it reviews the name after every user message using recent user-only context, changing it when the topic changes. It runs after the response, so its Utility Model call never delays the Main Model. Select **Only once** to name an unnamed chat from its first user message instead. Previously saved settings are preserved; switch existing **Only once** configurations to **After every user message** to enable topic updates.

Use `/rename New Chat Name` to rename the current chat directly, or `/rename auto` to generate and save a name with its configured Utility Model.

Subordinate chats keep their delegation labels. Automatic naming does not overwrite them; an explicit rename action or a new `call_subordinate` name can change them.
