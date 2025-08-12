# Available Secret Placeholders

You have access to the following secret placeholders that will be replaced with actual values during tool execution:
{{keys_list}}

Below is your current secrets file with values masked but comments preserved. Use it as documentation for what each secret is for:

```
{{secrets_content}}
```

**Important Guidelines:**
- Use the exact placeholder format: §§KEY_NAME§§ (double section sign markers)
- Secret values may contain special characters that need escaping in JSON strings
- Placeholders are case-sensitive and must match the exact key names
- These placeholders work in tool arguments but are automatically masked in responses and logs
