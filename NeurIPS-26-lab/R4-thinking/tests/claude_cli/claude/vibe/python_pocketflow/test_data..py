```python
TEST_INPUTS = [
    {
        "problem": (
            "A snail is at the bottom of a 30-foot well. "
            "Each day it climbs 3 feet and each night it slides back 2 feet. "
            "How many days does it take for the snail to reach the top?"
        ),
        "notes": "Classic off-by-one trap; tests whether the model correctly handles the final day.",
    },
    {
        "problem": (
            "You have two ropes, each of which takes exactly 1 hour to burn completely, "
            "but neither burns at a uniform rate. "
            "Using only these two ropes and a lighter, how do you measure exactly 45 minutes?"
        ),
        "notes": "Lateral-thinking / constraint puzzle; requires insight about burning both ends.",
    },
    {
        "problem": (
            "Three missionaries and three cannibals need to cross a river. "
            "There is one boat that can carry at most two people. "
            "If cannibals ever outnumber missionaries on either bank (or in the boat), "
            "the missionaries will be eaten. "
            "Find a sequence of crossings that gets everyone safely to the other side."
        ),
        "notes": "State-space search problem; multi-step planning with hard constraints.",
    },
]

if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, ".")
    from flow import run_thinking_workflow

    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    entry = TEST_INPUTS[idx]
    print(f"Running test input {idx}: {entry['notes']}\n")
    result = run_thinking_workflow(entry["problem"])
    print(json.dumps(
        {k: v for k, v in result.items() if k != "thinking_history"},
        indent=2,
    ))
```