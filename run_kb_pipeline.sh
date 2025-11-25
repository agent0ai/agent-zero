#!/bin/bash
# Complete Unity Knowledge Base Setup Pipeline
# Run this inside the agent-zero-unity container

echo "============================================================"
echo "🎮 UNITY KNOWLEDGE BASE - COMPLETE PIPELINE"
echo "============================================================"
echo ""

# Step 1: Scan Unity project
echo "📁 Step 1/4: Scanning Unity project..."
python3 /tmp/build_unity_kb.py
if [ $? -ne 0 ]; then
    echo "❌ Scanning failed!"
    exit 1
fi
echo ""

# Step 2: Create Qdrant collection
echo "🔧 Step 2/4: Setting up Qdrant collection..."
python3 /tmp/setup_qdrant_collection.py
if [ $? -ne 0 ]; then
    echo "❌ Collection setup failed!"
    exit 1
fi
echo ""

# Step 3: Ingest documents
echo "📤 Step 3/4: Ingesting documents to Qdrant..."
python3 /tmp/ingest_to_qdrant.py
if [ $? -ne 0 ]; then
    echo "❌ Ingestion failed!"
    exit 1
fi
echo ""

# Step 4: Test retrieval
echo "🔍 Step 4/4: Testing semantic search..."
python3 /tmp/test_search.py
echo ""

echo "============================================================"
echo "✅ UNITY KNOWLEDGE BASE SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Agent Zero can now:"
echo "  • Search Unity code semantically"
echo "  • Filter by assembly and code type"
echo "  • Find exact keyword matches"
echo "  • Retrieve full file context"
echo ""
echo "Access Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""
