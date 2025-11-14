# Vision Model Configuration

Agent Zero supports dedicated vision models for image analysis, allowing you to combine specialized vision models with your preferred chat models.

## Overview

By default, Agent Zero uses your chat model for vision tasks if it supports vision capabilities. However, you can configure a separate, dedicated vision model to handle image analysis independently.

This is particularly useful when:
* Your chat model doesn't support vision (e.g., text-only models)
* You want to use a specialized vision model (e.g., MiniCPM-V, GPT-4V) while using a different model for chat
* Running local setups with multiple models on different servers

## Configuration

### Vision Model Settings

Navigate to **Settings** → **Agent** tab to find the new **Vision Model** section:

* **Vision model provider**: Select your provider (supports all chat providers)
* **Vision model name**: Exact model name from your provider
* **Vision model API base URL**: API endpoint (for local/custom providers)
* **Vision model context length**: Maximum tokens for vision model
* **Rate Limiting**: Configure request and token limits
* **Additional parameters**: LiteLLM-compatible parameters

### Vision Strategy

Configure how vision is handled in two sections:

#### Chat Model
* **Supports Vision**: Toggle if your chat model has native vision
* **Vision Strategy**:
  * **Native**: Use chat model's vision (if "Supports Vision" is enabled)
  * **Dedicated**: Always use the dedicated vision model

#### Web Browser Model
* **Use Vision**: Toggle if your browser model has native vision
* **Vision Strategy**:
  * **Native**: Use browser model's vision (if "Use Vision" is enabled)
  * **Dedicated**: Always use the dedicated vision model

## Example Setup

### Local llamacpp Setup (Dedicated Vision Model)
```
Vision Model:
- Provider: Other OpenAI compatible
- Name: minicpm-v-4_5
- API Base: http://localhost:8083/v1

Chat Model:
- Provider: Other OpenAI compatible
- Name: oss-120b
- Supports Vision: Yes  ← Enable vision
- Vision Strategy: Dedicated  ← Use vision model
```

### Cloud Setup (Native Model Vision)
```
Chat Model:
- Provider: OpenAI
- Name: gpt-4-vision-preview
- Supports Vision: Yes  ← Enable vision
- Vision Strategy: Native  ← Use GPT-4V's own vision
```

## How It Works

### Native Strategy
When using native strategy with vision-capable models:
1. User uploads image
2. Image sent directly to chat/browser model
3. Model processes text and image together
4. Agent responds with combined understanding

### Dedicated Strategy
When using dedicated vision model:
1. User uploads image
2. Image sent to vision model for analysis
3. Vision model generates detailed text description
4. Description passed to chat model
5. Agent responds based on text description

> [!TIP]
> The dedicated strategy is ideal for combining powerful text models (like large parameter LLMs) with specialized vision models, optimizing both quality and cost.

## Troubleshooting

### Vision Model Not Responding
* Verify API base URL is correct
* Check that the model is running on your server
* Confirm API key is configured (if required)

### Images Not Being Analyzed
* Check Vision Strategy is set to "Dedicated"
* Verify Vision Model configuration is complete
* Review Agent Zero logs for error messages

### For llamacpp Users
If using llamacpp with vision models, ensure you've loaded the mmproj file:
```bash
./llama-server \
  --model /path/to/vision-model.gguf \
  --mmproj /path/to/vision-model-mmproj.gguf \
  --port 8083
```

> [!NOTE]
> The vision model feature is fully backwards compatible. Existing setups continue to work without modification, as the default strategy is "native".

## Benefits

* **Flexibility**: Mix and match text and vision models based on your needs
* **Cost Optimization**: Use affordable text models for chat, specialized models for vision
* **Local Control**: Run all models locally with full privacy
* **Quality**: Leverage best-in-class models for each specific task

For technical details about the implementation, see the source files in `python/tools/vision_load.py` and `python/helpers/settings.py`.
