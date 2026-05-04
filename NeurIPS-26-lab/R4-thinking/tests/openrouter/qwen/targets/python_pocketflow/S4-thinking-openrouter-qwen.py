import os
import json
import urllib.request

# SPL: CREATE FUNCTION assemble_prompt(state, plan)
# SPL: RETURNS TEXT AS $$
# SPL: You are executing a chain of thought for: {state} based on the plan: {plan}.
# SPL: Generate the next logical step in strict YAML format.
# SPL: If you need to continue the reasoning process, add the field CONTINUE: true.
# SPL: If the solution is ready, add the field FINAL: true.
# SPL: Do not wrap output in markdown. Don't add conversational filler.
# SPL: $$;
def assemble_prompt(state, plan):
    return f"""You are executing a chain of thought for: {state} based on the plan: {plan}.
Generate the next logical step in strict YAML format.
If you need to continue the reasoning process, add the field CONTINUE: true.
If the solution is ready, add the field FINAL: true.
Do not wrap output in markdown. Don't add conversational filler."""


class S3ThinkingOpenrouterQwen:
    """Minimalist ETL-style LLM orchestration workflow for chain-of-thought reasoning."""

    def __init__(self, api_key=None, model=None):
        model = model or os.environ.get("LLM_MODEL", "qwen/qwen3.6-plus")
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def _call_llm(self, prompt: str) -> str:
        if not self.api_key:
            raise EnvironmentError("OPENROUTER_API_KEY environment variable is required for GENERATE step.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "s3-thinking-openrouter-qwen"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(
            self.api_url, 
            json.dumps(payload).encode("utf-8"), 
            headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    # SPL: WORKFLOW ChainOfThoughtLoop
    # SPL:   INPUT @problem STRING, @plan STRING := "default_plan"
    # SPL:   OUTPUT @final_result STRING
    # SPL: DO
    def run(self, problem: str, plan: str = "default_plan") -> str:
        # SPL:   @state := "Init State: " + @problem + "\n" + "Plan: " + @plan;
        state = f"Init State: {problem}\nPlan: {plan}"
        
        # SPL:   @next_thought_needed := "true";
        next_thought_needed = "true"
        
        # SPL:   @final_result := "";
        final_result = ""
        
        # SPL:   @llm_output := "";
        llm_output = ""
        
        # SPL:   @iteration := 0;
        iteration = 0

        # SPL:   WHILE @next_thought_needed = "true" AND @iteration < 3 DO
        while next_thought_needed == "true" and iteration < 3:
            # SPL:     GENERATE assemble_prompt(@state, @plan) INTO @llm_output;
            prompt_text = assemble_prompt(state, plan)
            llm_output = self._call_llm(prompt_text)
            
            # SPL:     @iteration := @iteration + 1;
            iteration += 1

            # SPL:     EVALUATE @llm_output WHEN contains("YAML_ERROR") THEN
            if "YAML_ERROR" in llm_output:
                # SPL:       @next_thought_needed := "true";
                next_thought_needed = "true"
            # SPL:     ELSE
            else:
                # SPL:       EVALUATE @llm_output WHEN contains("CONTINUE: true") THEN
                if "CONTINUE: true" in llm_output:
                    # SPL:         @state := "Update State & Stream Progress: " + @state + "\n" + @llm_output;
                    state = f"Update State & Stream Progress: {state}\n{llm_output}"
                    # SPL:         @next_thought_needed := "true";
                    next_thought_needed = "true"
                # SPL:       ELSE
                else:
                    # SPL:         @final_result := "Extract Final Solution: " + @llm_output;
                    final_result = f"Extract Final Solution: {llm_output}"
                    # SPL:         @next_thought_needed := "false";
                    next_thought_needed = "false"
                # SPL:       END;
            # SPL:     END;
        # SPL:   END;

        # SPL:   CALL write_file("chain_of_thought.md", @final_result);
        with open("chain_of_thought.md", "w", encoding="utf-8") as f:
            f.write(final_result)

        # SPL:   RETURN @final_result WITH status = "complete";
        # SPL: END;
        return final_result


if __name__ == "__main__":
    workflow = S3ThinkingOpenrouterQwen()
    print("Starting ChainOfThoughtLoop...")
    output = workflow.run(problem="How can we reduce latency in transformer-based NLP models?")
    print(f"Workflow completed. Final output:\n{output}")