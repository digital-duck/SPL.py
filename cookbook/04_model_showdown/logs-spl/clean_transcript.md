Okay, I'll process these transcript snippets and normalize them. Normalization here means consolidating the information and presenting it in a structured format.

Here's the normalized output:

```json
[
  {
    "speaker": "Alice",
    "utterance": "We need to fix the login bug before Friday.  Also need to update the docs."
  },
  {
    "speaker": "Bob",
    "utterance": "I'll handle it."
  }
]
```

**Explanation of the Process & Normalization Choices:**

1. **Splitting by Speaker:**  I've separated each utterance based on the speaker's name (Alice and Bob).

2. **Combining Related Utterances:** I combined "We need to fix the login bug before Friday" and "also need to update the docs" into a single utterance for Alice for better context.

3. **Handling Unknown Input:** The "Unknown" input is simply ignored as there's no speaker or content.

4. **JSON Format:** The output is formatted as a JSON array, which is a common and easily parsable format for representing structured data. This makes it easy to use this data in other applications or systems.

**Notes:**

*   **Assumptions:** I've made some assumptions to create a reasonable normalization. For example, I've interpreted "I'll handle it" as Bob taking responsibility for the login bug.  More sophisticated normalization might involve natural language understanding (NLU) to better resolve ambiguous statements.
*   **Further Enhancement:**  A more advanced normalization system could:
    *   Identify tasks (e.g., "fix login bug", "update docs").
    *   Assign priorities (e.g., "before Friday").
    *   Extract entities (e.g., "login bug", "docs").

Let me know if you'd like me to adjust the normalization based on specific requirements (e.g., different output format, more detailed entity extraction).