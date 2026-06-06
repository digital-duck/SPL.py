
# conda activate spl123

# R1 ENV
export ADAPTER=openrouter   
export MODEL=claude
export MODEL_ID=anthropic/claude-sonnet-4.6
export RECIPE=agent
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S7
spl3 vibe \
  --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow
  
# R2 ENV
export ADAPTER=openrouter   
export MODEL=claude
export MODEL_ID=anthropic/claude-sonnet-4.6
export RECIPE=rag
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S7
spl3 vibe \
  --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow
  
# R3 ENV
export ADAPTER=openrouter   
export MODEL=claude
export MODEL_ID=anthropic/claude-sonnet-4.6
export RECIPE=judge
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S7
spl3 vibe \
  --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow
  
# R4 ENV
export ADAPTER=openrouter   
export MODEL=claude
export MODEL_ID=anthropic/claude-sonnet-4.6
export RECIPE=thinking
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S7
spl3 vibe \
  --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow
  
  
# R5 ENV
export ADAPTER=openrouter   
export MODEL=claude
export MODEL_ID=anthropic/claude-sonnet-4.6
export RECIPE=research
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL

# S7
spl3 vibe \
  --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow
  
  

