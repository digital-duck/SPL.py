import os
import sys
import yaml
import requests
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from pocketflow import Node, Flow

# --- Configuration ---
DEFAULT_MODEL = "google/gemini-2.0-flash-001"
MAX_ITERATIONS = 3

# --- LLM Helper ---

def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set.")
    
    print(f"Calling LLM ({model})...")
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/research-agent",
            "X-Title": "PocketFlow Research Agent",
        },
        json={
            "model": model, 
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        },
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"Error from OpenRouter: {resp.status_code} - {resp.text}")
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def robust_yaml_parse(raw_output: str) -> dict:
    """
    Parses YAML from LLM output. If it fails, attempts to wrap known keys 
    in block scalars to handle unquoted special characters.
    """
    cleaned = raw_output.replace("```yaml", "").replace("```", "").strip()
    try:
        return yaml.safe_load(cleaned)
    except yaml.YAMLError:
        # Fallback: force block scalar for search_query if parsing failed
        lines = cleaned.split('\n')
        fixed_lines = []
        for line in lines:
            if "search_query:" in line and "|" not in line:
                key, val = line.split(":", 1)
                fixed_lines.append(f"{key}: |")
                fixed_lines.append(f"  {val.strip()}")
            else:
                fixed_lines.append(line)
        try:
            return yaml.safe_load("\n".join(fixed_lines))
        except:
            return {"action": "answer"} # Default to termination on total failure

# --- Workflow Nodes ---

class DecideActionNode(Node):
    def prep(self, shared: dict):
        return shared["question"], shared.get("context", "No search results yet."), shared.get("iteration", 0)

    def exec(self, args):
        question, context, iteration = args
        
        # Safety cap
        if iteration >= MAX_ITERATIONS:
            print(f"[DECIDE] Max iterations ({MAX_ITERATIONS}) reached. Forcing answer.")
            return {"action": "answer", "reasoning": "Iteration limit reached."}

        prompt = f"""
        You are a research assistant. Based on the user question and accumulated context, 
        decide whether you need to perform a web search or if you have enough info to answer.

        USER QUESTION: {question}
        ACCUMULATED CONTEXT: {context}
        ITERATION: {iteration + 1} of {MAX_ITERATIONS}

        Output ONLY valid YAML in this format:
        action: "search" # or "answer"
        search_query: "specific query for duckduckgo" # only if action is search
        reasoning: "brief explanation"
        """
        raw = call_llm(prompt)
        return robust_yaml_parse(raw)

    def post(self, shared: dict, prep_res, exec_res):
        _, _, iteration = prep_res
        shared["iteration"] = iteration + 1
        shared["last_decision"] = exec_res
        
        action = exec_res.get("action", "answer")
        print(f"[DECISION] Action: {action} | Reasoning: {exec_res.get('reasoning')} | Iteration: {shared['iteration']}")
        return action

class SearchWebNode(Node):
    def prep(self, shared: dict):
        return shared["last_decision"].get("search_query")

    def exec(self, query):
        print(f"[SEARCH] Query: {query}")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            
            if not results:
                print(f"[SEARCH] No results found for: {query}")
                return "No results found."
                
            print(f"[SEARCH] Found {len(results)} results.")
            return "\n".join(f"- {r['title']}: {r['body']}" for r in results)
        except Exception as e:
            print(f"[SEARCH] Error: {str(e)}")
            return f"Search failed: {str(e)}"

    def post(self, shared: dict, prep_res, exec_res):
        current_context = shared.get("context", "")
        # Filter out empty results to avoid confusing the LLM
        if exec_res and exec_res != "No results found.":
            shared["context"] = current_context + f"\n\n--- Results for '{prep_res}' ---\n" + exec_res
        else:
            print(f"[SEARCH] Warning: Skipping context update for empty/failed search.")
        return "default"

class AnswerQuestionNode(Node):
    def prep(self, shared: dict):
        return shared["question"], shared.get("context", "No context found.")

    def exec(self, args):
        question, context = args
        prompt = f"""
        Synthesize a comprehensive final answer for the user based on the research context provided.
        
        QUESTION: {question}
        RESEARCH CONTEXT: {context}
        
        Final Answer:
        """
        return call_llm(prompt)

    def post(self, shared: dict, prep_res, exec_res):
        shared["answer"] = exec_res
        shared["status"] = "done"
        return "done"

# --- Main Execution ---

def run_research_agent(question: str):
    # Initialize Nodes
    decide = DecideActionNode()
    search = SearchWebNode()
    answer = AnswerQuestionNode()

    # Wire Workflow
    # WHILE loop: decide -> search -> decide
    decide - "search" >> search
    search >> decide
    
    # EXIT path: decide -> answer -> end
    decide - "answer" >> answer

    # Initialize shared state
    shared_state = {
        "question": question,
        "context": "",
        "iteration": 0,
        "status": "pending"
    }

    # Run Flow
    flow = Flow(start=decide)
    flow.run(shared_state)

    return shared_state

if __name__ == "__main__":
    if len(sys.argv) < 2:
        user_query = "What are the latest breakthroughs in room-temperature superconductivity as of 2024?"
    else:
        user_query = " ".join(sys.argv[1:])

    print(f"Starting Research Agent for: {user_query}\n" + "="*50)
    result = run_research_agent(user_query)
    
    print("\n" + "="*50)
    print("FINAL ANSWER:")
    print(result.get("answer"))
    print(f"\nStatus: {result.get('status')}")