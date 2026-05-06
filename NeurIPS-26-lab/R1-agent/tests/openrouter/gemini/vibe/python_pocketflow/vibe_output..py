import os
import yaml
import requests
from typing import Dict, Any
from duckduckgo_search import DDGS

# --- LLM Helper ---
def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls the LLM via OpenRouter/OpenAI compatible API.
    Reads configuration from environment variables.
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model = model or os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct")

    if not api_key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# --- Tool Implementation ---
def search_web_duckduckgo(query: str) -> str:
    """Performs a web search and returns a concatenated string of results."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            formatted = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            return formatted if formatted else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

# --- PocketFlow Node Base ---
class Node:
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return shared

    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return inputs

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> None:
        shared.update(exec_res)

# --- Workflow Nodes ---

class DecideAction(Node):
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
You are a Research Coordinator. Determine if the current context is sufficient to answer the question.
Question: {inputs.get('question')}
Current Context: {inputs.get('context', 'None')}

Respond ONLY in valid YAML format:
action: "search" | "answer"
reasoning: "your logic here"
search_query: "query if action is search, else null"
"""
        raw_response = call_llm(prompt)
        # Clean potential markdown blocks
        clean_response = raw_response.replace("```yaml", "").replace("```", "").strip()
        try:
            decision = yaml.safe_load(clean_response)
            return {"decision": decision}
        except Exception:
            # Fallback if LLM fails YAML
            return {"decision": {"action": "answer", "reasoning": "Error parsing LLM output"}}

class SearchWeb(Node):
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs['decision'].get('search_query')
        print(f"[*] Searching for: {query}")
        results = search_web_duckduckgo(query)
        
        new_context = inputs.get('context', "") + f"\n\nSearch Results for '{query}':\n{results}"
        return {"context": new_context}

class AnswerQuestion(Node):
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
Synthesize a final response based on the research gathered.
Question: {inputs.get('question')}
Research Context: {inputs.get('context')}

Provide a comprehensive, accurate, and well-formatted answer.
"""
        answer = call_llm(prompt)
        return {"answer": answer, "status": "done"}

# --- Workflow Orchestrator ---
class ResearchAgentFlow:
    def __init__(self):
        self.decide_node = DecideAction()
        self.search_node = SearchWeb()
        self.answer_node = AnswerQuestion()

    def run(self, question: str):
        # Initialize Shared State (@vars)
        shared = {
            "question": question,
            "context": "",
            "answer": None,
            "decision": None,
            "status": "running"
        }

        print(f"[!] Starting Research for: {question}")

        # WHILE loop logic
        max_iterations = 5
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            
            # 1. Decide Action
            prep_data = self.decide_node.prep(shared)
            exec_data = self.decide_node.exec(prep_data)
            self.decide_node.post(shared, prep_data, exec_data)

            action = shared['decision'].get('action')
            print(f"[+] Decision: {action} (Iteration {iterations})")

            # 2. EVALUATE / Branching
            if action == "search":
                prep_data = self.search_node.prep(shared)
                exec_data = self.search_node.exec(prep_data)
                self.search_node.post(shared, prep_data, exec_data)
                # Loops back to start of while
            else:
                # Break loop to Answer
                break
        
        # 3. Final Synthesis
        prep_data = self.answer_node.prep(shared)
        exec_data = self.answer_node.exec(prep_data)
        self.answer_node.post(shared, prep_data, exec_data)

        return shared['answer']

if __name__ == "__main__":
    # Example usage
    user_query = "What are the latest developments in room-temperature superconductivity as of late 2023 and 2024?"
    
    agent = ResearchAgentFlow()
    final_result = agent.run(user_query)
    
    print("\n" + "="*50)
    print("FINAL RESEARCH REPORT:")
    print("="*50)
    print(final_result)