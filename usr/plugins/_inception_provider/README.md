# Inception Labs Provider

This plugin adds an OpenAI‑compatible provider **Inception Labs** (model `mercury-2`) to Agent Zero.

## Installation
1. Clone the Agent Zero repository (or fork it) and navigate to the repository root.
2. Create the plugin directory structure:
   ```bash
   mkdir -p usr/plugins/_inception_provider/conf
   ```
3. Copy the following files into the new directory:
   - `plugin.yaml`
   - `conf/model_providers.yaml`
   - `README.md` (this file)
   - `LICENSE` (e.g., MIT)
4. Add the plugin to git, commit and push:
   ```bash
   git add usr/plugins/_inception_provider
   git commit -m "Add Inception Labs provider (mercury-2)"
   git push origin <your‑branch>
   ```
5. Open a Pull Request against the official `agent-zero` repository.

## Configuration
- **Provider ID**: `inception`
- **Provider Name**: `Inception Labs`
- **LitLLM Provider**: `openai`
- **Model**: `mercury-2`
- **API Base**: `https://api.inceptionlabs.ai/v1`
- **Required Secret**: `INCEPTION_API_KEY`

Set the secret in Agent Zero (e.g., via the UI or `a0-manage-plugin set-secret`). The plugin automatically reads the key from the environment variable `INCEPTION_API_KEY`.

## Usage
1. Open **Settings → Model Configuration**.
2. Select the **Cost Efficient** preset (or any other preset you wish to use).
3. Choose **Chat Provider** → `Inception Labs`.
4. Set **Chat Model** → `mercury-2`.
5. Save the changes.
6. The model will now be available for chat, utility, or embedding tasks depending on the preset configuration.



