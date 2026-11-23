### browser

Use the selected browser for rendered pages, interaction, files, and DevTools. The `cdp` action and the other Browser actions work on the same browser. For plain text research prefer the web-search skill or document_query.

For rendered browsing, first load `browser-automation` with `skills_tool:load`. For fragile forms, `browser-automation` links to `browser-form-workflows`. Use the actions listed for this chat.

For an existing tab, list tabs first and reuse its `browser_id`. Ground interactions in fresh page refs or a selector. Close only tabs you created. The browser does not automatically load screenshots. Use `vision_load` with the returned `vision_load.tool_args.paths` before reasoning visually.
