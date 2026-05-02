from anthropic import Anthropic
import os

import sys
from pathlib import Path
# [SPL-SHIM-ON]
# SPL shim: set SPL_ADAPTER (ollama|claude_cli) and SPL_MODEL env vars
# Revert: change 'if False' back to 'if True' in the block below
sys.path.insert(0, str(Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.name == 'utils' else Path(__file__).resolve().parents[1]))
from call_llm_shim import call_llm
# [SPL-SHIM-OFF]

if False:  # [SPL-SHIM] original — revert: change to 'if True'
    def call_llm(prompt):
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key"))
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=6000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
if __name__ == "__main__":
    print("## Testing call_llm")
    prompt = "In a few words, what is the meaning of life?"
    print(f"## Prompt: {prompt}")
    response = call_llm(prompt)
    print(f"## Response: {response}")