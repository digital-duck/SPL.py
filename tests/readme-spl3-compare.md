spl3 compare \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/S2-rag-claude_cli-sonnet.mmd \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S2-rag-openrouter-gemini.mmd \
--adapter claude_cli --format html -o /tmp/spl3/r2-rag-mmd-diff.html

xdg-open /tmp/spl3/r2-rag-mmd-diff.html &

spl3 compare \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/S2-rag-claude_cli-sonnet.mmd \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S2-rag-openrouter-gemini.mmd \
--mode llm \
--adapter claude_cli --format html -o /tmp/spl3/r2-rag-mmd-diff.html

xdg-open /tmp/spl3/r2-rag-mmd-diff-llm.html &


spl3 compare \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/S3-rag-claude_cli-sonnet.spl \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/openrouter/gemini/S3-rag-openrouter-gemini.spl \
--adapter claude_cli --format html -o /tmp/spl3/r2-rag-spl-diff.html

xdg-open /tmp/spl3/r2-rag-spl-diff.html &

spl3 compare \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/S1-rag-claude_cli-sonnet-1-spec.md \
/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/S5-rag-claude_cli-sonnet-2-spec.md \
--mode llm \
--adapter claude_cli --format html -o /tmp/spl3/r2-rag-spec-diff.html

xdg-open /tmp/spl3/r2-rag-spec-diff.html &
