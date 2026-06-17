#!/bin/bash
# Pull all ollama models required for recipe-77 experiments

set -e

# Models extracted from run_experiment.py MODELS dict (excluding claude_cli)
MODELS=(
    "gemma3"
    "gemma4:e2b"
    "qwen2.5"
    "deepseek-v2:16b"
    "phi3"
    "phi4"
    "llama3.2"
    "lfm2.5"
    "rnj-1"
)

echo "Pulling ollama models for recipe-77..."
echo "Total models to fetch: ${#MODELS[@]}"
echo ""

for model in "${MODELS[@]}"; do
    echo "► Pulling $model..."
    ollama pull "$model"
    echo "  ✓ $model ready"
    echo ""
done

echo "Done! All models are ready for recipe-77 experiments."
