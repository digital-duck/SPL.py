import os
import requests
from typing import Dict, Any
from duckduckgo_search import DDGS
# Note: assuming pocketflow is available in the environment or path
try:
    from pocketflow import Node, Flow
except ImportError:
    # Fallback to local pocketflow if available
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[3] / "cookbook/05_self_refine"))
    from pocketflow import Node, Flow

# --- LLM Functions (SPL Functions) ---

def call_llm(prompt: str) -> str:
    """Helper to route to OpenRouter Gemini"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/digital-duck/SPL.py", # Required by OpenRouter
        "X-Title": "SPL.py PocketFlow Agent"
    }
    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# SPL: CREATE FUNCTION DecideAction(context TEXT, question TEXT)
def decide_action_fn(context: str, question: str) -> str:
    prompt = f"""
Based on the question and current context, decide if more information is needed.
Return 'search' if you need to look up more information.
Return 'answer' if you have enough information to provide the final answer.
Context: {context}
Question: {question}
"""
    return call_llm(prompt)

# SPL: CREATE FUNCTION AnswerQuestion(context TEXT, question TEXT)
def answer_question_fn(context: str, question: str) -> str:
    prompt = f"""
Provide a comprehensive answer to the question based on the provided context.
Context: {context}
Question: {question}
"""
    return call_llm(prompt)

# --- Real Tool Implementation ---

# SPL: CALL web_search(@question)
def web_search(query: str) -> str:
    """Real DuckDuckGo search implementation"""
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return f"No results found for: {query}"
        
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            url   = r.get("href", "")
            body  = r.get("body", "")
            lines.append(f"[{i}] {title}\n    URL: {url}\n    {body}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"

# --- Workflow Nodes ---

class SearchAndAnswerWorkflow(Flow):
    # SPL: WORKFLOW SearchAndAnswer
    # SPL: INPUT @question TEXT
    
    def __init__(self, question: str):
        super().__init__()
        self.state = {
            "question": question,
            "context": f"Original question: {question}", # SPL: @context := 'Original question: ' + @question
            "action": "search",                            # SPL: @action := 'search'
            "iteration": 0,                                # SPL: @iteration := 0
            "max_iterations": 3,                           # SPL: @max_iterations := 3
            "answer": None,
            "status": "in_progress"
        }

    def run(self):
        # SPL: WHILE @iteration < @max_iterations DO
        while self.state["iteration"] < self.state["max_iterations"]:
            
            # SPL: GENERATE DecideAction(@context, @question) INTO @action
            self.state["action"] = decide_action_fn(self.state["context"], self.state["question"])
            
            # SPL: EVALUATE @action
            if "search" in self.state["action"].lower(): # SPL: WHEN contains('search')
                # SPL: CALL web_search(@question) INTO @search_results
                search_results = web_search(self.state["question"])
                
                # SPL: @context := @context + '\n\nSearch Results:\n' + @search_results
                self.state["context"] += f"\n\nSearch Results:\n{search_results}"
                
                # SPL: @iteration := @iteration + 1
                self.state["iteration"] += 1
            else:
                # SPL: ELSE (implicitly 'answer')
                # SPL: GENERATE AnswerQuestion(@context, @question) INTO @answer
                self.state["answer"] = answer_question_fn(self.state["context"], self.state["question"])
                self.state["status"] = "complete"
                
                # SPL: RETURN @answer WITH status = 'complete', iterations = @iteration
                return {"answer": self.state["answer"], "status": self.state["status"], "iterations": self.state["iteration"]}

        # SPL: -- Fallback in case max iterations reached
        # SPL: GENERATE AnswerQuestion(@context, @question) INTO @answer
        self.state["answer"] = answer_question_fn(self.state["context"], self.state["question"])
        self.state["status"] = "max_iterations"
        
        # SPL: RETURN @answer WITH status = 'max_iterations', iterations = @iteration
        return {"answer": self.state["answer"], "status": self.state["status"], "iterations": self.state["iteration"]}

# Execution Block
if __name__ == "__main__":
    # Ensure OPENROUTER_API_KEY is set in environment
    user_question = "What is machine learning?"
    agent = SearchAndAnswerWorkflow(question=user_question)
    result = agent.run()
    print(f"\nStatus: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    print(f"\nAnswer:\n{result['answer']}")
