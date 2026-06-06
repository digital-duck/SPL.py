import os
import json
import yaml
import requests
from typing import Dict, Any

# --- PocketFlow Minimalist ETL-style Framework ---

class Node:
    def __init__(self):
        self.next_node = None

    def __rshift__(self, other):
        self.next_node = other
        return other

    def exec(self, shared: Dict[str, Any]):
        raise NotImplementedError

class Flow:
    def __init__(self, start_node: Node):
        self.start_node = start_node

    def run(self, shared: Dict[str, Any]):
        current = self.start_node
        while current:
            next_node = current.exec(shared)
            # If the node returns a specific next node (for branching/loops), follow it
            # Otherwise, follow the default sequence defined by >>
            current = next_node if next_node else current.next_node
        return shared

# --- Utilities & LLM Adapter ---

def call_llm(prompt: str) -> str:
    """
    OpenRouter compatible LLM call using Gemini 3 Flash.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "your_api_key_here")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def search_web_duckduckgo(query: str) -> str:
    """
    Mock Web Search Tool (Simulates CALL search_web_duckduckgo).
    In a real production env, use a library like duckduckgo-search.
    """
    print(f"--- CALLING SEARCH: {query} ---")
    # Simulated search result for demonstration
    return f"\n[Search Result for '{query}']: Found information regarding the specific details of the topic including current status and key figures.\n"

# --- Workflow Nodes ---

class DecideAction(Node):
    """
    The 'Brain' node. Uses YAML output to decide between searching or answering.
    """
    def exec(self, shared: Dict[str, Any]):
        prompt = f"""
        You are a Research Controller. 
        User Question: {shared['question']}
        Current Context: {shared['context']}

        Decide if you need more information or if you can answer now.
        Output your decision in the following YAML format:
        ```yaml
        thinking: "brief explanation of your logic"
        action: "search" or "answer"
        reason: "why you chose this"
        search_query: "query if searching"
        ```
        """
        response = call_llm(prompt)
        
        # Extract YAML block
        try:
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)
        except:
            # Fallback
            decision = {"action": "answer"}

        shared["decision"] = decision
        
        if decision.get("action") == "search":
            shared["query"] = decision.get("search_query", shared['question'])
            return self.search_node # Branch to Search
        else:
            return self.answer_node # Branch to Answer

class SearchTool(Node):
    """
    Executes the search and appends to context.
    """
    def exec(self, shared: Dict[str, Any]):
        result = search_web_duckduckgo(shared["query"])
        shared["context"] += f"\n- {result}"
        # Loop back to decide
        return self.decide_node

class AnswerQuestion(Node):
    """
    Synthesizes the final answer.
    """
    def exec(self, shared: Dict[str, Any]):
        prompt = f"""
        You are an expert Research Assistant.
        Original Question: {shared['question']}
        Gathered Research: {shared['context']}

        Provide a comprehensive, markdown-formatted final answer based ONLY on the research provided.
        """
        shared["answer"] = call_llm(prompt)
        return None # End of flow

# --- Workflow Construction ---

def create_research_flow():
    # Initialize Nodes
    decide = DecideAction()
    search = SearchTool()
    answer = AnswerQuestion()

    # Define Wiring (State Machine logic)
    decide.search_node = search
    decide.answer_node = answer
    search.decide_node = decide # Create the WHILE loop

    return Flow(decide)

# --- Main Execution ---

if __name__ == "__main__":
    # 1. Setup Shared State
    initial_state = {
        "question": "What are the latest breakthroughs in room-temperature superconductivity as of 2024?",
        "context": "No previous search.",
        "answer": None
    }

    # 2. Initialize and Run Flow
    research_agent = create_research_flow()
    final_state = research_agent.run(initial_state)

    # 3. Return / Output Results
    print("\n" + "="*50)
    print("FINAL RESEARCH REPORT")
    print("="*50)
    print(f"Question: {final_state['question']}")
    print("\n--- Answer ---\n")
    print(final_state["answer"])
    print("\n--- Research History ---")
    print(final_state["context"])