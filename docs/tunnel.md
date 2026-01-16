# Remote Access to Magui via Flare Tunnel

Magui includes a built-in tunneling capability powered by [Flare](https://github.com/soulteary/flare), allowing you to securely expose your local instance to the internet.

## Why use a tunnel with Magui?

1. **Access from anywhere**: Control your Magui instance from work, while traveling, or from a different location.
2. **Mobile access**: Use Magui on your smartphone or tablet while on the go.
3. **Share with others**: Give temporary access to your Magui instance to colleagues or friends.
4. **Webhook integration**: Connect external services to Magui via webhooks.
5. **MCP Server**: Use Magui as an MCP server for other agents running on different machines.

## Using the Tunnel Feature

1. Open the settings and navigate to the "External Services" tab
2. Click on "Flare Tunnel" in the navigation menu
3. Click the "Create Tunnel" button to generate a new tunnel
4. Once created, the tunnel URL will be displayed and can be copied to share with others
5. The tunnel URL will remain active until you stop the tunnel or close the Magui application

## Security Considerations

When sharing your Magui instance via a tunnel:

- Anyone with the URL can access your Magui instance
- No additional authentication is added beyond what your Magui instance already has
- Consider setting up authentication if you're sharing sensitive information
- The tunnel exposes your local Magui instance, not your entire system

## Troubleshooting

If you encounter issues with the tunnel feature:

1. Check your internet connection
2. Try refreshing the tunnel URL
3. Restart Magui
4. Check the console logs for any error messages

## Adding Authentication

To add basic authentication to your Magui instance when using tunnels, you can set the following environment variables:

```
AUTH_LOGIN=your_username
AUTH_PASSWORD=your_password
```

Alternatively, you can configure the username and password directly in the settings:

1. Open the settings modal in the Magui UI
2. Navigate to the "External Services" tab
3. Find the "Authentication" section
4. Enter your desired username and password in the "UI Login" and "UI Password" fields
5. Click the "Save" button to apply the changes

This will require users to enter these credentials when accessing your tunneled Magui instance. When attempting to create a tunnel without authentication configured, Magui will display a security warning.