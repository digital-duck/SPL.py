```python
TEST_INPUTS = [
    {
        "question": (
            "What are the key differences between transformer and mamba "
            "architectures for long-sequence modeling?"
        ),
        "description": "Technical ML comparison — expects 2–3 search rounds",
    },
    {
        "question": (
            "What caused the 2023 Silicon Valley Bank collapse, "
            "and what regulatory changes followed?"
        ),
        "description": "Recent financial event — expects 2–4 search rounds",
    },
    {
        "question": (
            "What are the latest approved treatments for triple-negative "
            "breast cancer as of 2024?"
        ),
        "description": "Medical/clinical query — expects 3–5 search rounds for specificity",
    },
]

# To run all three sequentially:
if __name__ == "__main__":
    from research_agent import run_research_agent

    for case in TEST_INPUTS:
        print(f"\n{'#' * 70}")
        print(f"# {case['description']}")
        print(f"{'#' * 70}")
        answer = run_research_agent(case["question"])
        print(answer)
        print()
```