#!/bin/bash
# Fix the models.py file to handle Google provider correctly

echo "========================================="
echo "FIXING MODELS.PY ROOT CAUSE"
echo "========================================="

# Create a patch for models.py
docker exec agent-zero-container sh -c "cat > /tmp/fix_models.py << 'EOF'
import fileinput
import sys

# Fix the LiteLLMEmbeddingWrapper initialization
with open('/a0/models.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    # Fix embedding model name construction
    if 'self.model_name = f\"{provider}/{model}\" if provider != \"openai\" else model' in line:
        # For google provider with embeddings, don't add prefix
        lines[i] = '        self.model_name = f\"{provider}/{model}\" if provider not in [\"openai\", \"google\"] else model\\n'
        print(f'Fixed line {i+1}: Embedding model name construction')

    # Fix chat model name construction
    if 'model_value = f\"{provider}/{model}\"' in line:
        # For google provider, check if model already has gemini/ prefix
        lines[i-1] = '        # For google provider, don\\'t double-prefix if model already has gemini/\\n'
        lines[i] = '        if provider == \"google\" and model.startswith(\"gemini/\"):\\n'
        lines.insert(i+1, '            model_value = model\\n')
        lines.insert(i+2, '        else:\\n')
        lines.insert(i+3, '            model_value = f\"{provider}/{model}\"\\n')
        print(f'Fixed line {i+1}: Chat model name construction')
        break

# Write the fixed file
with open('/a0/models.py', 'w') as f:
    f.writelines(lines)

print('models.py has been patched!')
EOF

python3 /tmp/fix_models.py"

echo ""
echo "Verifying the fix..."
docker exec agent-zero-container sh -c "grep -A3 'self.model_name = f' /a0/models.py | head -10"

echo ""
echo "Restarting container..."
docker restart agent-zero-container

sleep 15

echo ""
echo "========================================="
echo "FIX APPLIED!"
echo "========================================="
echo ""
echo "The models.py file has been patched to:"
echo "1. Not add 'google/' prefix to embedding models"
echo "2. Not double-prefix chat models that already have 'gemini/'"
echo ""

if curl -s http://localhost:50001/health > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:50001/"
else
    echo "⚠️ Server is starting..."
fi