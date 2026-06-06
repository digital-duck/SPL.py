## 0. High-level Description

This workflow implements a research agent that uses a WHILE loop pattern to iteratively decide between web search and question answering until sufficient information is gathered. The workflow defines three CREATE FUNCTION prompts: a decision-making function that evaluates current context and returns either "search" or "answer" actions, a web search function that retrieves information via CALL tool, and a final answer generation function that synthesizes research into a comprehensive response. The control flow uses EVALUATE constructs to branch on the decision function's output - routing to either web search (which loops back to decision-making) or final answer generation (which terminates with RETURN). The workflow maintains shared state through @context and @search_query variables that accumulate research findings across iterations. Exception handling manages YAML parsing errors in the decision function's structured output, and the workflow includes side-effects via CALL for web search API integration and optional file output.

## 1. Purpose

This implementation creates an autonomous research agent that iteratively searches the web and synthesizes information to provide comprehensive answers to user questions.

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---------------|--------------------------------|-------|
| WORKFLOW | `Flow(start=decide)` | Entry point and node orchestration |
| CREATE FUNCTION | `Node.exec()` method | Each Node class contains a prompt template |
| GENERATE | `call_llm(prompt)` | LLM invocation with prompt string |
| CALL | `search_web_duckduckgo(query)` | Side-effect tool for web search |
| WHILE | `decide - "search" >> search` + `search - "decide" >> decide` | Cyclic node connections create loop |
| EVALUATE | `decide - "action" >> target_node` | Conditional routing based on LLM output |
| @variables | `shared` dictionary | Persistent state across nodes |
| RETURN WITH | `shared["answer"] = exec_res` + flow termination | Final result storage |
| EXCEPTION WHEN | `try/except` in `parse_yaml_safely()` | YAML parsing error recovery |

## 3. Logical Functions / Prompts

**DecideAction Function**
- Role: Strategic decision-making between search and answer actions
- Key conventions: YAML output format with `|` block scalars, structured thinking/reason/action fields
- Scoring: Binary classification (search/answer) based on context sufficiency

**SearchWeb Function** 
- Role: Web information retrieval via DuckDuckGo API
- Key conventions: Query string input, structured results with Title/URL/Snippet format
- Output: Formatted search results appended to context

**AnswerQuestion Function**
- Role: Final synthesis of research into comprehensive answer
- Key conventions: Question + research context input, natural language response
- Output: Complete answer ready for user consumption

## 4. Control Flow

Initial step: GENERATE DecideAction with current @context and @question → EVALUATE decision output WHEN contains('search') THEN route to SearchWeb, update @search_query → CALL web search tool, append results to @context → loop back to DecideAction → EVALUATE WHEN contains('answer') THEN route to AnswerQuestion → GENERATE final synthesis → RETURN WITH status=complete, answer=@final_response. The WHILE loop continues until DecideAction determines sufficient information exists to provide a quality answer.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a research agent that uses a WHILE loop pattern to iteratively decide between web search and question answering until sufficient information is gathered. The workflow defines three CREATE FUNCTION prompts: a decision-making function that evaluates current context and returns either 'search' or 'answer' actions, a web search function that retrieves information via CALL tool, and a final answer generation function that synthesizes research into a comprehensive response. The control flow uses EVALUATE constructs to branch on the decision function's output - routing to either web search (which loops back to decision-making) or final answer generation (which terminates with RETURN). The workflow maintains shared state through @context and @search_query variables that accumulate research findings across iterations. Exception handling manages YAML parsing errors in the decision function's structured output, and the workflow includes side-effects via CALL for web search API integration and optional file output." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph  
spl3 splc compile <output.spl> --lang go
```