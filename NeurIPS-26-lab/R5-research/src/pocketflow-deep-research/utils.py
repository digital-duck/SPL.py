import os
from duckduckgo_search import DDGS

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
        """Call LLM — auto-detects OpenAI or Gemini based on available API key."""
        if os.environ.get("OPENAI_API_KEY"):
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            r = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return r.choices[0].message.content
        elif os.environ.get("GEMINI_API_KEY"):
            from google import genai
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return r.text
        else:
            raise ValueError("Set OPENAI_API_KEY or GEMINI_API_KEY")
    
def search_web(query, max_results=3):
    results = DDGS().text(query, max_results=max_results)
    return "\n\n".join([f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for r in results])

if __name__ == "__main__":
    print("## Testing call_llm")
    prompt = "In a few words, what is the meaning of life?"
    print(f"## Prompt: {prompt}")
    response = call_llm(prompt)
    print(f"## Response: {response}")

    print("\n## Testing search_web")
    query = "latest AI research breakthroughs 2025"
    print(f"## Query: {query}")
    results = search_web(query)
    print(f"## Results: {results}")
