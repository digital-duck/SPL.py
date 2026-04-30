# PocketFlow Research Agent

A minimalist ETL-style LLM orchestration implementation of a research agent that can iteratively search and synthesize information to answer questions.

## Setup Instructions

1. Install Python 3.7+
2. No additional dependencies required for basic functionality
3. Optional: Install your preferred LLM client (OpenAI, Anthropic, etc.) and modify the `_default_llm_client()` method

```bash
# Optional LLM client installation
pip install openai  # or anthropic, etc.
```

## Run Command

```bash
python pocketflow_agent.py
```

## Expected Output Pattern

```
Question: What are the latest developments in quantum computing?
Answer: Mock response to: Based on all the research gathered, provide a comp...
Metadata: {'status': 'complete', 'iterations': 2}
```

## SPL to Python Mapping

| SPL Construct | Python Equivalent | Notes |
|---------------|-------------------|-------|
| `CREATE FUNCTION` | `def method_name(self, ...)` | Class methods with prompt templates |
| `WORKFLOW research_agent` | `def research_agent(self, ...)` | Main workflow method |
| `INPUT @question TEXT, @max_iterations INTEGER := 3` | `def research_agent(self, question: str, max_iterations: int = 3)` | Method parameters with defaults |
| `OUTPUT @answer TEXT` | `return answer, metadata` | Return tuple with result and metadata |
| `@variable := value` | `variable = value` | Variable assignment |
| `WHILE @iteration < @max_iterations DO` | `while iteration < max_iterations:` | Standard while loop |
| `GENERATE function(@args) INTO @var` | `var = self.function(args)` | Method call with assignment |
| `EVALUATE @decision WHEN contains(...)` | `if self.contains(decision, ...)` | Conditional evaluation |
| `CALL sub_workflow(@args) INTO @var` | `var = self.sub_workflow(args)` | Method call |
| `EXCEPTION WHEN ErrorType THEN` | `except Exception as e: if 'ErrorType' in ...` | Exception handling with type checking |
| `RETRY` | `continue` | Loop continuation |
| `RETURN @var WITH status = 'value'` | `return var, {'status': 'value'}` | Return with metadata |