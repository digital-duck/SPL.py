(spl123) papagame@papa-game:~/projects/digital-duck/SPL.py$ spl3 run cookbook/65_llm_splc/llm_splc.spl     --adapter claude_cli     --tools cookbook/65_llm_splc/tools.py     --param spl_file="$(pwd)/cookbook/63_parallel_code_review/parallel_code_review.spl"     --param target="autogen"     --param output_file="$(pwd)/cookbook/65_llm_splc/targets/autogen/parallel_code_review.py"
INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/65_llm_splc/llm_splc.spl
Registry: ['llm_splc']
Loaded 62 tool(s) from cookbook/65_llm_splc/tools.py
Running workflow: llm_splc(['spl_file', 'target', 'output_file'])
[INFO] llm_splc start | file=/home/papagame/projects/digital-duck/SPL.py/cookbook/63_parallel_code_review/parallel_code_review.spl target=autogen model=claude-cli
[INFO] Generating {target} implementation ...
INFO:spl.executor:GENERATE segment 1 (compile_prompt) -> 2090 tokens, 139142ms
INFO:spl.executor:GENERATE chain done -> @implementation (8360 chars total)
[INFO] Reviewing against SPL spec ...
INFO:spl.executor:GENERATE segment 1 (review_prompt) -> 275 tokens, 112444ms
INFO:spl.executor:GENERATE chain done -> @review (1101 chars total)
[WARN] Gaps found — applying fixes ...
INFO:spl.executor:GENERATE segment 1 (fix_prompt) -> 2402 tokens, 65199ms
INFO:spl.executor:GENERATE chain done -> @implementation (9610 chars total)
[INFO] Fixed implementation generated
[INFO] Output written to /home/papagame/projects/digital-duck/SPL.py/cookbook/65_llm_splc/targets/autogen/parallel_code_review.py
[INFO] llm_splc complete | target=autogen
INFO:spl.executor:RETURN: 9610 chars | status=complete, target=autogen, spl_file=/home/papagame/projects/digital-duck/SPL.py/cookbook/63_parallel_code_review/parallel_code_review.spl

Status:  complete
Output:  ```python
import asyncio
import logging
from typing import Dict, Any, Optional, List
import autogen
from autogen import AssistantAgent, UserProxyAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelCodeReview:
    def __init__(self, review_model: str = "gemma4"):
        self.review_model = review_model

        # Configure LLM for Ollama - style reviewer (400 tokens)
        style_llm_config = {
            "config_list": [
                {
                    "model": review_model,
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "ollama",
                }
            ],
            "temperature": 0.1,
            "max_tokens": 400,
        }

        # Configure LLM for Ollama - security auditor (400 tokens)
        security_llm_config = {
            "config_list": [
                {
                    "model": review_model,
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "ollama",
                }
            ],
            "temperature": 0.1,
            "max_tokens": 400,
        }

        # Configure LLM for Ollama - test generator (512 tokens)
        test_llm_config = {
            "config_list": [
                {
                    "model": review_model,
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "ollama",
                }
            ],
            "temperature": 0.1,
            "max_tokens": 512,
        }

        # Configure LLM for Ollama - report merger (1024 tokens)
        merge_llm_config = {
            "config_list": [
                {
                    "model": review_model,
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "ollama",
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        # Create specialized agents for each review type
        self.style_reviewer = AssistantAgent(
            name="style_reviewer",
            system_message="You are a senior code engineer conducting style and correctness reviews.",
            llm_config=style_llm_config,
            max_consecutive_auto_reply=1,
        )

        self.security_auditor = AssistantAgent(
            name="security_auditor",
            system_message="You are a security engineer conducting static analysis.",
            llm_config=security_llm_config,
            max_consecutive_auto_reply=1,
        )

        self.test_generator = AssistantAgent(
            name="test_generator",
            system_message="You are a test engineer writing unit tests.",
            llm_config=test_llm_config,
            max_consecutive_auto_reply=1,
        )

        self.report_merger = AssistantAgent(
            name="report_merger",
            system_message="You are a senior engineering lead consolidating code review reports.",
            llm_config=merge_llm_config,
            max_consecutive_auto_reply=1,
        )

        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )

    def _style_review_prompt(self, code: str, lang: str) -> str:
        return f"""You are a senior {lang} engineer conducting a code review focused on
style, readability, and correctness.

Review the following {lang} code:

{code}

Provide feedback on:
1. Naming conventions and clarity
2. Code structure and organisation
3. Potential logic errors or edge cases
4. Adherence to idiomatic {lang} patterns

Format: numbered list, most important issues first.
Keep your review under 200 words."""

    def _security_audit_prompt(self, code: str, lang: str) -> str:
        return f"""You are a security engineer conducting a static analysis of {lang} code.

Review the following {lang} code for security vulnerabilities:

{code}

Check for (where applicable):
1. Injection risks (SQL, command, path traversal)
2. Insecure input validation or missing bounds checks
3. Hard-coded credentials or secrets
4. Insecure use of cryptographic primitives
5. Race conditions or unsafe concurrency
6. Excessive permissions or privilege escalation paths

Format: numbered list, CRITICAL issues first, then MODERATE, then LOW.
If no issues found, say "No security issues detected."
Keep your audit under 200 words."""

    def _test_generator_prompt(self, code: str, lang: str) -> str:
        return f"""You are a test engineer writing unit tests for {lang} code.

Generate unit test cases for the following {lang} code:

{code}

Requirements:
- Cover the happy path (expected inputs and outputs)
- Cover at least two edge cases (empty input, boundary values, None/null, etc.)
- Cover at least one error/exception path if applicable
- Use the standard testing framework for {lang}
  (pytest for Python, testing package for Go, jest for TypeScript/JavaScript)

Output only the test code, no explanation. Include import statements."""

    def _merge_reviews_prompt(self, style: str, sec_audit: str, tests: str) -> str:
        return f"""You are a senior engineering lead consolidating three independent code-review reports
into a single, actionable plan.

Style & Correctness Review:
{style}

Security Audit:
{sec_audit}

Generated Test Cases:
{tests}

Produce a consolidated report with three sections:
1. **Action Items** — numbered list of changes to make, CRITICAL first, then MODERATE, then LOW
2. **Test Coverage** — paste the generated tests verbatim under a code block
3. **Summary** — one paragraph overall assessment (is this code production-ready?)

Keep the Action Items section under 150 words."""

    async def _get_agent_response(self, agent: AssistantAgent, message: str) -> str:
        """Get response from a specific agent"""
        try:
            chat_result = self.user_proxy.initiate_chat(
                agent,
                message=message,
                max_turns=1,
                silent=True
            )

            # Extract the last message from the agent
            if chat_result.chat_history:
                for msg in reversed(chat_result.chat_history):
                    if msg.get('name') == agent.name and msg.get('content'):
                        return msg['content']

            return "[ERROR] No response from agent"

        except Exception as e:
            logger.error(f"Error getting response from {agent.name}: {str(e)}")
            return f"[ERROR] Agent {agent.name} failed: {str(e)}"

    async def run_parallel_review(self, code: str, lang: str = "python", log_dir: str = "cookbook/63_parallel_code_review/logs-spl") -> str:
        """Run parallel code review workflow - main entry point"""
        try:
            logger.info(f"[parallel_code_review] starting 3-way parallel review | lang={lang} review_model={self.review_model}")

            # Prepare prompts for each reviewer
            style_prompt = self._style_review_prompt(code, lang)
            security_prompt = self._security_audit_prompt(code, lang)
            test_prompt = self._test_generator_prompt(code, lang)

            # Run three reviews in parallel - equivalent to CALL PARALLEL in SPL
            tasks = [
                self._get_agent_response(self.style_reviewer, style_prompt),
                self._get_agent_response(self.security_auditor, security_prompt),
                self._get_agent_response(self.test_generator, test_prompt)
            ]

            # Wait for all parallel reviews to complete
            style_fb, sec_fb, test_fb = await asyncio.gather(*tasks)

            logger.info("[parallel_code_review] parallel checks complete — merging into report")

            # Generate final consolidated report using merge function
            merge_prompt = self._merge_reviews_prompt(style_fb, sec_fb, test_fb)
            report = await self._get_agent_response(self.report_merger, merge_prompt)

            logger.info(f"[parallel_code_review] done | report_len={len(report)}")
            return report

        except Exception as e:
            # Exception handling equivalent to SPL EXCEPTION WHEN blocks
            if "model unavailable" in str(e).lower() or "unavailable" in str(e).lower():
                logger.error(f"[parallel_code_review] model unavailable: {self.review_model}")
                return "[ERROR] Model unavailable."
            elif "budget exceeded" in str(e).lower() or "token" in str(e).lower() or "max_tokens" in str(e).lower():
                logger.warning("[parallel_code_review] token budget exceeded during merge")
                return report if 'report' in locals() else "[ERROR] Budget exceeded during processing"
            else:
                raise

def parallel_code_review(code: str, lang: str = "python", review_model: str = "gemma4", log_dir: str = "cookbook/63_parallel_code_review/logs-spl") -> str:
    """Main function equivalent to SPL workflow parallel_code_review"""
    reviewer = ParallelCodeReview(review_model)
    return asyncio.run(reviewer.run_parallel_review(code, lang, log_dir))

if __name__ == "__main__":
    # Usage example matching SPL INPUT defaults
    sample_code = "def add(a, b): return a - b"

    print("Running parallel code review...")
    print(f"Code: {sample_code}")
    print("=" * 60)

    try:
        result = parallel_code_review(sample_code)
        print("Review Report:")
        print("=" * 50)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
```
LLM calls: 3  Latency: 316788ms
Log:     /home/papagame/.spl/logs/llm_splc-claude_cli-20260420-183613.md
