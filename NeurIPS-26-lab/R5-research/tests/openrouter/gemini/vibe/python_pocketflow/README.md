# Recursive Map-Reduce Research Agent (PocketFlow)

## Overview
This project implements a **recursive map-reduce research agent** using a minimalist ETL-style orchestration logic. It automates deep research by iteratively generating search queries, performing parallel web searches, extracting facts, and synthesizing a final markdown report.

## Requirements
- Python 3.8+
- `requests`
- `pyyaml`

```bash
pip install requests pyyaml
```

## Setup
Set your API key and preferred model as environment variables:

```bash
export OPENROUTER_API_KEY='your_api_key_here'
export LLM_MODEL='google/gemini-2.0-flash-001' # Optional
```

## Usage
Run the script directly:
```bash
python research_agent.py
```

## Workflow Logic
1. **PlannerNode**: Takes the topic and generates 3 distinct search queries using the LLM. 
2. **ResearcherNode (Map Phase)**: Executes the 3 queries in parallel threads.
3. **ResearcherNode (Tool Call)**: Uses a `search_web` function to simulate gathering data from the internet.
4. **ResearcherNode (Reduce Phase)**: Summarizes the raw search results into concise facts and appends them to the shared `notes`.
5. **SynthesizerNode (Evaluate)**: Checks if the research is complete. 
    - If gaps exist and the loop limit (2) isn't reached, it returns `action: research`.
    - Otherwise, it returns `action: finalize` and generates the final Markdown report.
6. **Loop**: The process repeats based on the Synthesizer's decision.