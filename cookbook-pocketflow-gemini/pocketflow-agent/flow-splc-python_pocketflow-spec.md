Looking at this Python PocketFlow implementation, I can see it's a research agent with a decision loop pattern. Let me create the functional specification:

## 0. High-level Description

This workflow implements a research agent that uses an iterative search-and-decide pattern to answer complex questions. The WORKFLOW starts with a decision-making CREATE FUNCTION that analyzes the current question and research context to determine whether to search for more information or provide a final answer. When the decision is to search, it executes a CALL to a web search tool and accumulates results in a shared context variable, then returns to the decision point using WHILE loop logic. When sufficient information is gathered, the workflow uses EVALUATE logic to branch to an answer-generation CREATE FUNCTION that synthesizes the research into a comprehensive response. The multi-step process uses GENERATE calls for LLM reasoning at decision and answer points, maintains shared state across iterations, and includes EXCEPTION handling for YAML parsing failures. The workflow terminates with RETURN when a satisfactory answer is produced.

## 1. Purpose

This implementation creates an autonomous research agent that iteratively searches the web and synthesizes information to provide comprehensive answers to complex questions.

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---------------|--------------------------------|-------|
| WORKFLOW | `Flow(start=decide)` | Entry point and flow orchestration |
| CREATE FUNCTION | `Node` classes (DecideAction, SearchWeb, AnswerQuestion) | Reusable prompt templates and logic units |
| GENERATE | `call_llm(prompt)` in `exec()` methods | LLM calls for reasoning and text generation |
| CALL | `search_web_duckduckgo(query)` | Side-effect tool calls (web search) |
| @variables | `shared` dictionary | Persistent state across workflow steps |
| WHILE condition | `search - "decide" >> decide` | Loop back to decision node |
| EVALUATE | `decide - "search" >> search` / `decide - "answer" >> answer` | Conditional branching based on LLM output |
| RETURN | `return "done"` in AnswerQuestion | Workflow termination with result |
| EXCEPTION | YAML parsing retry logic in DecideAction | Error handling for malformed responses |

## 3. Logical Functions / Prompts

**DecideAction**
- **Role**: Decision-making controller that determines next workflow step
- **Key conventions**: Returns YAML with `action`, `thinking`, `reason`, `answer`, `search_query` fields; uses block scalar `|` notation for multi-line text; includes action space documentation in prompt

**SearchWeb** 
- **Role**: Side-effect executor for web information gathering
- **Key conventions**: No LLM prompt; pure tool call using DuckDuckGo API; formats results as "Title/URL/Snippet" structure

**AnswerQuestion**
- **Role**: Final synthesis and answer generation
- **Key conventions**: Uses research context to generate comprehensive answer; simple prompt structure with context and question sections

## 4. Control Flow

Initial step: DecideAction analyzes question and empty context → WHILE loop condition: if action equals "search" → execute SearchWeb CALL → accumulate results in @context → return to DecideAction → EVALUATE: if action equals "answer" → execute AnswerQuestion GENERATE → RETURN WITH answer in shared state and status="done".

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a research agent that uses an iterative search-and-decide pattern to answer complex questions. The WORKFLOW starts with a decision-making CREATE FUNCTION that analyzes the current question and research context to determine whether to search for more information or provide a final answer. When the decision is to search, it executes a CALL to a web search tool and accumulates results in a shared context variable, then returns to the decision point using WHILE loop logic. When sufficient information is gathered, the workflow uses EVALUATE logic to branch to an answer-generation CREATE FUNCTION that synthesizes the research into a comprehensive response. The multi-step process uses GENERATE calls for LLM reasoning at decision and answer points, maintains shared state across iterations, and includes EXCEPTION handling for YAML parsing failures. The workflow terminates with RETURN when a satisfactory answer is produced." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph  
spl3 splc compile <output.spl> --lang go
```