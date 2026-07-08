#!/usr/bin/env bash
# Generate the English Morphology concept-book in Chinese (@language=zh).
# Same domain graph as the existing English book - illustrates the
# @language parameter for the multilingual claim in the SPL-for-Education
# paper (§7.5 -> result). Runs locally via ollama/gemma4 - no API cost.
#
# Usage:
#   cd /home/gongai/projects/digital-duck/SPL.py
#   ./cookbook/74_concept_book/generate_english_morphology_zh.sh

set -euo pipefail

source /home/gongai/anaconda3/etc/profile.d/conda.sh
conda activate spl123

cd /home/gongai/projects/digital-duck/SPL.py
mkdir -p cookbook/74_concept_book/output/html

export SPL_WHILE_MAX_ITER=50  # english_morphology has 31 concepts - bump from default
export SPL_MAX_LLM_CALLS=50   # 33 concepts + 1 capstone = 34 calls minimum; default cap is 25

spl3 run cookbook/74_concept_book/build_concept_book.spl \
  --tools cookbook/74_concept_book/tools.py \
  --param domain_yaml=english_morphology_graph.yaml \
  --param target=morphological_decoding_principle \
  --param language=zh \
  --param output_html=cookbook/74_concept_book/output/html/english_morphology_concept_book_zh.html \
  --adapter ollama -m gemma4
