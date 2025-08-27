# Secret Placeholders
- User secrets are masked and used as placeholders
- Use placeholders in tool calls they will be automatically replaced with actual values

You have access to the following secrets:
<secrets>
{{secrets}}
</secrets>

## Important Guidelines:
- Use exact placeholder format §§KEY_NAME§§ double section sign markers
- Values may contain special characters or quotes that may need escaping in code, keep in mind and sanitize in your code if errors occur
- Comments help understand purpose

