## Tools available:

{{tools}}

## Remarks about calling tools
Tool calls must always be valid json.
Tool arguments can contain special placeholders:

### Copy/paste last tool output
- Include the full output of the previous tool call inside any `tool_args` field by inserting the literal token `{last_tool_output}`. It will be replaced automatically before the tool executes.
- Check the [EXTRAS] section for a preview and the originating `tool_name`.
- !! Never repeat the full output of a tool call if it is possible to copy&paste it.
Example for copying the output of the last tool call into the response tool arguments:
~~~json
{
  "thoughts": [
    "Acknowledge system warning about JSON formatting.",
    "Send properly formatted reply using the response tool.",
    "Include the previously collected terminal output by inserting the {last_tool_output} token to avoid duplicating raw text manually."
  ],
  "tool_name": "response",
  "tool_args": {
    "text": "Here is the terminal output you requested:\n\n{last_tool_output}"
  }
}
~~~
