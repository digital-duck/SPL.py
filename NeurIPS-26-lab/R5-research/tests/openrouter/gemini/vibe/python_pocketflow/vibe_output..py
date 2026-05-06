import os
import yaml
import json
import requests
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

# --- LLM Helper ---
def call_llm(prompt: str, model: str = None) -> str:
    """
    Standard LLM call helper. 
    Reads API key from OPENROUTER_API_KEY or OPENAI_API_KEY.
    """
    model = model or os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001")
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.")

    # Using OpenRouter/OpenAI compatible chat completion
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

# --- Tools ---
def search_web(query: str) -> str:
    """
    Performs a web search using DuckDuckGo (via a simple API wrapper or scraping logic).
    For reliability in this script, we use a public API-less approach or a mock 
    if the environment is restricted, but here we implement a standard mockable search.
    """
    print(f"  [Tool] Searching web for: {query}")
    try:
        # Using a simple duckduckgo-style search call (mocking the return for stability)
        # In a production env, use 'duckduckgo_search' pip package
        return f"Search results for {query}: [Fact 1 about {query}], [Fact 2 about {query}]."
    except Exception as e:
        return f"Search failed for {query}: {str(e)}"

# --- PocketFlow Node Base ---
class Node:
    def prep(self, shared: Dict) -> Dict: return shared
    def exec(self, inputs: Dict) -> Dict: return {}
    def post(self, shared: Dict, prep_res: Dict, exec_res: Dict) -> Dict: return shared

# --- Workflow Nodes ---

class PlannerNode(Node):
    def exec(self, inputs: Dict) -> Dict:
        topic = inputs.get("topic")
        feedback = inputs.get("feedback", "Initial planning phase.")
        prompt = f"""
        Topic: {topic}
        Feedback from previous step: {feedback}
        
        Generate 3 diverse search queries to research this topic deeply.
        Respond ONLY in YAML format like this:
        queries:
          - "query 1"
          - "query 2"
          - "query 3"
        """
        response = call_llm(prompt)
        # Clean markdown code blocks if present
        clean_response = response.replace("```yaml", "").replace("```", "").strip()
        data = yaml.safe_load(clean_response)
        return {"queries": data.get("queries", [])}

    def post(self, shared: Dict, prep_res: Dict, exec_res: Dict) -> Dict:
        shared["current_queries"] = exec_res["queries"]
        return shared

class ResearcherNode(Node):
    def exec(self, inputs: Dict) -> Dict:
        queries = inputs.get("current_queries", [])
        
        def process_query(q):
            raw_results = search_web(q)
            prompt = f"Extract key facts about the topic '{inputs.get('topic')}' from these search results: {raw_results}. Be concise."
            return call_llm(prompt)

        # Map phase: Parallel execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            facts = list(executor.map(process_query, queries))
        
        # Reduce phase: Combine facts
        return {"new_notes": "\n".join(facts)}

    def post(self, shared: Dict, prep_res: Dict, exec_res: Dict) -> Dict:
        if "notes" not in shared: shared["notes"] = ""
        shared["notes"] += "\n" + exec_res["new_notes"]
        return shared

class SynthesizerNode(Node):
    def exec(self, inputs: Dict) -> Dict:
        topic = inputs.get("topic")
        notes = inputs.get("notes")
        loop_count = inputs.get("loop_count", 0)
        
        prompt = f"""
        Topic: {topic}
        Collected Research: {notes}
        Iteration: {loop_count}
        
        Evaluate the research. If there are major gaps and iteration < 2, set action to 'research'.
        If the information is sufficient or we reached the limit, set action to 'finalize' and write a markdown report.
        
        Respond ONLY in YAML format:
        action: "research" or "finalize"
        feedback: "what is missing?"
        report: "Full markdown report if finalizing, else null"
        """
        response = call_llm(prompt)
        clean_response = response.replace("```yaml", "").replace("```", "").strip()
        return yaml.safe_load(clean_response)

    def post(self, shared: Dict, prep_res: Dict, exec_res: Dict) -> Dict:
        shared["action"] = exec_res.get("action", "finalize")
        shared["feedback"] = exec_res.get("feedback", "")
        shared["report"] = exec_res.get("report", "")
        shared["loop_count"] = shared.get("loop_count", 0) + 1
        return shared

# --- Workflow Engine ---

def run_deep_research(topic: str):
    # Initialize Shared State
    shared = {
        "topic": topic,
        "notes": "",
        "loop_count": 0,
        "action": "research",
        "feedback": "Initial search",
        "report": ""
    }
    
    planner = PlannerNode()
    researcher = ResearcherNode()
    synthesizer = SynthesizerNode()

    print(f"Starting Research Workflow for: {topic}")

    # WHILE Loop with EVALUATE logic
    while shared["action"] == "research" and shared["loop_count"] <= 2:
        print(f"\n--- Iteration {shared['loop_count']} ---")
        
        # 1. Plan
        print("Planning queries...")
        p_res = planner.exec(shared)
        shared = planner.post(shared, {}, p_res)
        
        # 2. Research (Map-Reduce)
        print(f"Researching {len(shared['current_queries'])} queries...")
        r_res = researcher.exec(shared)
        shared = researcher.post(shared, {}, r_res)
        
        # 3. Synthesize & Evaluate
        print("Synthesizing results...")
        s_res = synthesizer.exec(shared)
        shared = synthesizer.post(shared, {}, s_res)
        
        print(f"Decision: {shared['action']}")

    print("\n--- Workflow Complete ---")
    return shared["report"]

if __name__ == "__main__":
    # Example Input
    target_topic = "The impact of quantum computing on modern cryptography"
    final_report = run_deep_research(target_topic)
    
    print("\nFINAL REPORT:\n")
    print(final_report)