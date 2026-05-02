Looking at this Python — PocketFlow implementation, I'll create a functional specification that maps back to SPL constructs.

## 0. High-level Description

This WORKFLOW implements a judge-generator pattern for iterative product description refinement using two reusable CREATE FUNCTION components. The Generator function takes a product task and optional feedback to GENERATE a compelling product description using structured YAML output format. The Judge function evaluates the generated description and returns a score, verdict, and improvement feedback. The workflow uses a WHILE loop controlled by attempt counting (maximum 3 iterations) and EVALUATE logic that branches on the judge's pass/fail verdict — if the score is below 7 or verdict is "FAIL", the workflow loops back to the generator with the judge's feedback for improvement. The workflow maintains shared state variables for the current draft, attempt count, and feedback across iterations. Upon reaching maximum attempts or receiving a "PASS" verdict, the workflow terminates with RETURN containing the final description and score metadata. Both LLM calls use YAML-structured prompts with clear output formatting requirements, and the workflow includes EXCEPTION handling for parsing and retry logic with configurable wait times.

## 1. Purpose

Automatically generates and iteratively refines product descriptions through AI-powered judge feedback until achieving acceptable quality or reaching maximum attempts.

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---------------|-------------------------------|-------|
| WORKFLOW <name> | `Flow(start=generator)` | Flow class with connected nodes defines the workflow |
| CREATE FUNCTION <name> | `class Generator(Node)`, `class Judge(Node)` | Node classes with exec() method contain prompt logic |
| GENERATE <fn>(...) INTO @<var> | `call_llm(prompt)` + result assignment | LLM calls store results in shared state |
| CALL <tool>(...) INTO @<var> | File I/O in main() with `Path(out).write_text()` | Side-effect operations like saving output |
| WHILE <cond> DO ... END | Node connection `judge - "fail" >> generator` | Loop via conditional routing based on return values |
| EVALUATE @<var> WHEN contains('...') THEN ... | `if verdict.upper() == "PASS" or score >= 7:` | Conditional branching on LLM output |
| RETURN @<var> WITH <k>=<v> | `shared["final_description"]`, `shared["final_score"]` | Final results with metadata in shared state |
| EXCEPTION WHEN <Type> | `max_retries=3, wait=10` on nodes | Built-in retry and error handling configuration |
| @variables (shared state) | `shared` dictionary | Persistent state passed between nodes |

## 3. Logical Functions / Prompts

**Generator Function**
- **Name**: Product Description Generator
- **Role**: Creates compelling 2-3 sentence product descriptions with optional feedback incorporation
- **Key conventions**: YAML response format with `description:` field, feedback integration when provided, clear task specification

**Judge Function**  
- **Name**: Description Quality Evaluator
- **Role**: Scores descriptions 1-10 for clarity/persuasiveness and provides improvement feedback
- **Key conventions**: YAML output with `score`, `reasoning`, `verdict` (PASS/FAIL), and `feedback` fields; score threshold of 7 for passing

## 4. Control Flow

**Initial step**: Generator creates initial product description from task input → **Loop condition**: WHILE attempts < 3 AND judge verdict == "FAIL" → **Branch logic**: EVALUATE judge output score and verdict; if score >= 7 OR verdict == "PASS" then accept, else increment attempts and provide feedback to generator → **Termination**: RETURN WITH final_description and final_score when max attempts reached or description passes evaluation.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements a judge-generator pattern for iterative product description refinement using two reusable CREATE FUNCTION components. The Generator function takes a product task and optional feedback to GENERATE a compelling product description using structured YAML output format. The Judge function evaluates the generated description and returns a score, verdict, and improvement feedback. The workflow uses a WHILE loop controlled by attempt counting (maximum 3 iterations) and EVALUATE logic that branches on the judge's pass/fail verdict — if the score is below 7 or verdict is 'FAIL', the workflow loops back to the generator with the judge's feedback for improvement. The workflow maintains shared state variables for the current draft, attempt count, and feedback across iterations. Upon reaching maximum attempts or receiving a 'PASS' verdict, the workflow terminates with RETURN containing the final description and score metadata. Both LLM calls use YAML-structured prompts with clear output formatting requirements, and the workflow includes EXCEPTION handling for parsing and retry logic with configurable wait times." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```