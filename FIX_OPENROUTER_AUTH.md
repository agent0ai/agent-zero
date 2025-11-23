# Fixing OpenRouter Authentication Error in Agent Zero

## Problem
You're getting a `401 Unauthorized` error from OpenRouter:
```
litellm.exceptions.AuthenticationError: AuthenticationError: OpenrouterException - {"error":{"message":"No auth credentials found","code":401}}
```

## Solution Options

### Option 1: Get and Configure OpenRouter API Key (Recommended)

1. **Get an OpenRouter API Key**:
   - Go to https://openrouter.ai/
   - Sign up/Login to your account
   - Navigate to API Keys section
   - Create a new API key

2. **Add to your `.env` file**:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here
   ```

3. **Restart Agent Zero** to load the new environment variable

### Option 2: Use Alternative AI Providers

If you don't want to use OpenRouter, you can configure Agent Zero to use other providers:

#### A. OpenAI
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-your_openai_key_here
   ```
3. Update Agent Zero configuration to use OpenAI models

#### B. Anthropic (Claude)
1. Get API key from https://console.anthropic.com/
2. Add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   ```

#### C. Groq (Fast inference)
1. Get API key from https://console.groq.com/
2. Add to `.env`:
   ```bash
   GROQ_API_KEY=gsk_your_groq_key_here
   ```

#### D. Local Models (Ollama)
1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Configure Agent Zero to use local models

### Option 3: Change Model Configuration

Edit your Agent Zero configuration to use a different provider. Check the initialization files:
- `run_ui.py` or `run_cli.py`
- Look for model provider settings
- Change from `openrouter` to your preferred provider

### Option 4: Use Free/Local Options

For testing without API keys:
1. **Ollama** (local):
   ```bash
   # Install Ollama
   # Pull a model
   ollama pull mistral
   # Configure Agent Zero to use ollama/mistral
   ```

2. **Google Gemini** (free tier available):
   - Get API key from https://makersuite.google.com/app/apikey
   - Add `GOOGLE_API_KEY=your_key_here` to `.env`

## Quick Fix Steps

1. **Edit `.env` file** (already updated above)
2. **Replace placeholder** with actual API key:
   ```
   OPENROUTER_API_KEY=sk-or-v1-[your-actual-key-here]
   ```
3. **Save the file**
4. **Restart Agent Zero**

## Verification

After adding your API key:
1. Restart your Agent Zero application
2. The error should be resolved
3. You should be able to interact with the AI models

## Important Notes

- Never commit API keys to version control
- Keep your `.env` file in `.gitignore`
- OpenRouter provides access to multiple models with a single API key
- Consider setting up rate limiting if using paid APIs

## Still Having Issues?

1. **Check environment variable loading**:
   ```python
   import os
   print(os.getenv('OPENROUTER_API_KEY'))
   ```

2. **Verify API key format**:
   - OpenRouter keys typically start with `sk-or-v1-`
   - Ensure no extra spaces or quotes

3. **Test API key directly**:
   ```bash
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```

4. **Check Agent Zero logs** for more detailed error messages