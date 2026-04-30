import asyncio
import re
import yaml
from typing import Dict, Any, Tuple
import click


def _build_llm_client(adapter: str, model: str | None):
    """Return a synchronous generate(prompt) wrapper around spl.adapters."""
    try:
        from spl.adapters import get_adapter
    except ImportError:
        raise SystemExit("ERROR: spl.adapters not found. Run from the SPL.py virtualenv.")
    try:
        llm = get_adapter(adapter, **{"model": model} if model else {})
    except ValueError as exc:
        raise SystemExit(f"ERROR: {exc}")

    class _Client:
        def generate(self, prompt: str) -> str:
            async def _run():
                result = await llm.generate(prompt)
                return result.content
            return asyncio.run(_run())

    return _Client()


class PocketFlowAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    # SPL: CREATE FUNCTION decide_action(question TEXT, context TEXT) RETURNS TEXT
    def decide_action(self, question: str, context: str) -> str:
        prompt = f"""Based on the current research question and accumulated context, decide the next action.
Return your decision in this exact YAML format:

action: search|answer
reasoning: brief explanation
search_query: specific query (only if action is search)

Question: {question}
Current context: {context}

If you have sufficient information to provide a comprehensive answer, choose "answer".
If you need more specific information, choose "search" and provide a focused search query."""
        
        return self.llm_client.generate(prompt)
    
    # SPL: CREATE FUNCTION search_web(query TEXT) RETURNS TEXT
    def search_web(self, query: str) -> str:
        prompt = f"Search for: {query}"
        return self.llm_client.generate(prompt)
    
    # SPL: CREATE FUNCTION generate_final_answer(question TEXT, context TEXT) RETURNS TEXT
    def generate_final_answer(self, question: str, context: str) -> str:
        prompt = f"""Based on all the research gathered, provide a comprehensive answer to the question.

Question: {question}
Research context: {context}

Provide a detailed, well-structured response that synthesizes all available information."""
        
        return self.llm_client.generate(prompt)
    
    def extract_entities(self, decision: str) -> str:
        """Extract search query from decision YAML"""
        try:
            # Parse YAML-like content
            lines = decision.strip().split('\n')
            for line in lines:
                if 'search_query:' in line:
                    return line.split('search_query:', 1)[1].strip()
            return "general search"
        except Exception:
            return "general search"
    
    def web_search(self, query: str) -> str:
        """Simple web search wrapper"""
        return self.search_web(query)
    
    def contains(self, text: str, pattern: str) -> bool:
        """Helper function for EVALUATE conditions"""
        return pattern in text
    
    # SPL: WORKFLOW research_agent
    def research_agent(self, question: str, max_iterations: int = 3) -> Tuple[str, Dict[str, Any]]:
        # SPL: @iteration := 0; @context := ''; @search_query := '';
        iteration = 0
        context = ''
        search_query = ''
        
        # SPL: WHILE @iteration < @max_iterations DO
        while iteration < max_iterations:
            try:
                # SPL: GENERATE decide_action(@question, @context) INTO @decision;
                decision = self.decide_action(question, context)
                
                # SPL: EVALUATE @decision
                if self.contains(decision, 'action: search'):
                    # SPL: @iteration := @iteration + 1;
                    iteration += 1
                    # SPL: GENERATE extract_entities(@decision) INTO @query_data;
                    query_data = self.extract_entities(decision)
                    # SPL: CALL web_search(@query_data) INTO @search_results;
                    search_results = self.web_search(query_data)
                    # SPL: @context := @context + '\n' + @search_results;
                    context = context + '\n' + search_results
                    
                elif self.contains(decision, 'action: answer'):
                    # SPL: GENERATE generate_final_answer(@question, @context) INTO @answer;
                    answer = self.generate_final_answer(question, context)
                    # SPL: RETURN @answer WITH status = 'complete', iterations = @iteration;
                    return answer, {'status': 'complete', 'iterations': iteration}
                    
                else:
                    # SPL: ELSE clause
                    iteration += 1
                    context = context + '\nDecision parsing failed, continuing search.'
                    
            # SPL: EXCEPTION handlers
            except Exception as e:
                error_type = type(e).__name__
                if 'Hallucination' in error_type:
                    # SPL: WHEN HallucinationDetected THEN
                    iteration += 1
                    context = context + '\nRetrying due to hallucination detected.'
                elif 'ModelOverload' in error_type:
                    # SPL: WHEN ModelOverloaded THEN RETRY;
                    continue
                else:
                    raise e
        
        # SPL: GENERATE generate_final_answer(@question, @context) INTO @answer;
        try:
            answer = self.generate_final_answer(question, context)
            # SPL: RETURN @answer WITH status = 'max_iterations', iterations = @iteration;
            return answer, {'status': 'max_iterations', 'iterations': iteration}
            
        # SPL: EXCEPTION WHEN BudgetExceeded THEN
        except Exception as e:
            if 'Budget' in str(e):
                answer = self.generate_final_answer(question, context)
                return answer, {'status': 'budget_exceeded'}
            else:
                raise e

@click.command()
@click.option("--question", required=True, help="Research question to answer.")
@click.option("--max-iterations", default=3, show_default=True, help="Max search iterations.")
@click.option("--adapter", default="openrouter", show_default=True, help="LLM adapter name.")
@click.option("--model", default=None, help="Model override (adapter default if omitted).")
def main(question: str, max_iterations: int, adapter: str, model: str | None):
    llm_client = _build_llm_client(adapter, model)
    agent = PocketFlowAgent(llm_client=llm_client)
    answer, metadata = agent.research_agent(question, max_iterations=max_iterations)
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print(f"Metadata: {metadata}")

if __name__ == "__main__":
    main()