# Remote Control

Access Agent Zero from another computer or your phone with a shareable link.

Open **Remote Control** from the menu or plugin settings, choose a provider, and click **Start**. Open the resulting link on another device or scan its QR code with your phone. First-time setup can take a little longer; later starts reuse the installation.

Cloudflare Tunnel is the quickest way to get a link. Microsoft Dev Tunnels and Tailscale may ask you to sign in or approve access. Serveo is also available.

A login and password in **Settings → Authentication** are required before starting Remote Control. Anyone with the link can reach the sign-in page while remote access is active. Click **Stop** when finished.

The provider selector is the main setting. **Advanced** contains the optional target port; leave it at 0 to connect to Agent Zero automatically.

Active remote access resumes after Agent Zero restarts, although the link may change. Stopping or disabling keeps your provider setup; uninstalling removes it and any saved provider credentials.
