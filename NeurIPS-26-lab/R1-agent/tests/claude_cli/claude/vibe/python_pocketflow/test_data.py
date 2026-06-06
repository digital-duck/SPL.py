```python
test_inputs = [
    # 1. Current events requiring 2–3 search rounds
    "What were the main outcomes of the COP30 climate summit in 2025?",

    # 2. Technical question likely resolved in 1–2 searches
    "What is the difference between transformer attention mechanisms and state-space models like Mamba?",

    # 3. Multi-faceted question that exercises the full loop
    "Which countries have announced national AI sovereignty strategies in 2024-2025 and what are their key policy differences?",
]

# Run any of these as:
#   python research_agent.py "What were the main outcomes of the COP30 climate summit in 2025?"
# or drive programmatically:
if __name__ == "__main__":
    from research_agent import build_flow

    question = test_inputs[0]
    shared = {"question": question, "context": "", "iteration": 0}
    build_flow().run(shared)
    print(shared["answer"])
```