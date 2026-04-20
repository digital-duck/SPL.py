(spl123) papagame@papa-game:~/projects/digital-duck/SPL.py$ spl3 run cookbook/65_llm_splc/llm_splc.spl     --adapter claude_cli     --tools cookbook/65_llm_splc/tools.py     --param spl_file="$(pwd)/cookbook/63_parallel_code_review/parallel_code_review.spl"     --param target="crewai"     --param output_file="$(pwd)/cookbook/65_llm_splc/targets/crewai/parallel_code_review.py"
INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/65_llm_splc/llm_splc.spl
Registry: ['llm_splc']
Loaded 62 tool(s) from cookbook/65_llm_splc/tools.py
Running workflow: llm_splc(['spl_file', 'target', 'output_file'])
[INFO] llm_splc start | file=/home/papagame/projects/digital-duck/SPL.py/cookbook/63_parallel_code_review/parallel_code_review.spl target=crewai model=claude-cli
[INFO] Generating {target} implementation ...
INFO:spl.executor:GENERATE segment 1 (compile_prompt) -> 1915 tokens, 80409ms
INFO:spl.executor:GENERATE chain done -> @implementation (7661 chars total)
[INFO] Reviewing against SPL spec ...
INFO:spl.executor:GENERATE segment 1 (review_prompt) -> 223 tokens, 24047ms
INFO:spl.executor:GENERATE chain done -> @review (893 chars total)
[WARN] Gaps found — applying fixes ...
INFO:spl.executor:GENERATE segment 1 (fix_prompt) -> 2278 tokens, 150705ms
INFO:spl.executor:GENERATE chain done -> @implementation (9115 chars total)
[INFO] Fixed implementation generated
[INFO] Output written to /home/papagame/projects/digital-duck/SPL.py/cookbook/65_llm_splc/targets/crewai/parallel_code_review.py
[INFO] llm_splc complete | target=crewai
INFO:spl.executor:RETURN: 9115 chars | status=complete, target=crewai, spl_file=/home/papagame/projects/digital-duck/SPL.py/cookbook/63_parallel_code_review/parallel_code_review.spl

Status:  complete
Output:  ```python
import logging
from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def style_review(code: str, lang: str = "python", review_model: str = "gemma4", log_dir: str = "") -> str:
    """Style review workflow - simulates IMPORT '00_style_review'"""
    agent = Agent(
        role="Code Style & Correctness Reviewer",
        goal="Analyze code for style issues, bugs, and correctness problems",
        backstory="You are an expert code reviewer focused on style guidelines, best practices, and correctness. You catch bugs, style violations, and suggest improvements.",
        verbose=False,
        allow_delegation=False
    )

    task = Task(
        description=f"""
        Review the following {lang} code for style and correctness issues:

        ```{lang}
        {code}
        ```

        Analyze for:
        - Code style violations
        - Potential bugs or logical errors
        - Best practice violations
        - Readability issues
        - Performance concerns

        Provide specific, actionable feedback.
        """,
        expected_output="Detailed style and correctness review with specific issues and recommendations",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=0,
        process=Process.sequential
    )

    result = crew.kickoff()
    return str(result)

def security_audit(code: str, lang: str = "python", review_model: str = "gemma4", log_dir: str = "") -> str:
    """Security audit workflow - simulates IMPORT '01_security_audit'"""
    agent = Agent(
        role="Security Auditor",
        goal="Identify security vulnerabilities and risks in code",
        backstory="You are a cybersecurity expert specializing in code security audits. You identify vulnerabilities, security anti-patterns, and potential attack vectors.",
        verbose=False,
        allow_delegation=False
    )

    task = Task(
        description=f"""
        Perform a security audit of the following {lang} code:

        ```{lang}
        {code}
        ```

        Look for:
        - Security vulnerabilities
        - Injection flaws
        - Authentication/authorization issues
        - Data validation problems
        - Cryptographic weaknesses
        - Information disclosure risks

        Provide specific security recommendations.
        """,
        expected_output="Security audit report with identified vulnerabilities and mitigation strategies",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=0,
        process=Process.sequential
    )

    result = crew.kickoff()
    return str(result)

def test_generator(code: str, lang: str = "python", review_model: str = "gemma4", log_dir: str = "") -> str:
    """Test generator workflow - simulates IMPORT '02_test_generator'"""
    agent = Agent(
        role="Test Case Generator",
        goal="Generate comprehensive test cases for the given code",
        backstory="You are a QA engineer expert at creating thorough test cases. You generate unit tests, edge cases, and integration tests to ensure code quality.",
        verbose=False,
        allow_delegation=False
    )

    task = Task(
        description=f"""
        Generate comprehensive test cases for the following {lang} code:

        ```{lang}
        {code}
        ```

        Create:
        - Unit tests for normal cases
        - Edge case tests
        - Error condition tests
        - Integration tests if applicable
        - Performance tests if relevant

        Provide complete, runnable test code.
        """,
        expected_output="Complete set of test cases with runnable test code",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=0,
        process=Process.sequential
    )

    result = crew.kickoff()
    return str(result)

class ParallelCodeReview:
    def __init__(self, review_model: str = "gemma4"):
        self.review_model = review_model

    def merge_reviews(self, style: str, sec_audit: str, tests: str) -> str:
        """Merge function with token budget constraint"""
        agent = Agent(
            role="Senior Engineering Lead",
            goal="Consolidate multiple code review reports into actionable plans",
            backstory="You are a senior engineering lead with expertise in consolidating technical feedback into prioritized action items.",
            verbose=False,
            allow_delegation=False
        )

        # Enforce token budget by truncating inputs if needed
        max_input_length = 800  # Leave room for output budget of 1024 tokens
        if len(style) > max_input_length:
            style = style[:max_input_length] + "..."
        if len(sec_audit) > max_input_length:
            sec_audit = sec_audit[:max_input_length] + "..."
        if len(tests) > max_input_length:
            tests = tests[:max_input_length] + "..."

        task = Task(
            description=f"""
            You are a senior engineering lead consolidating three independent code-review reports
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

            Keep the Action Items section under 150 words.
            IMPORTANT: Keep total response under 1024 tokens.
            """,
            expected_output="Consolidated code review report with prioritized action items, test coverage, and summary (max 1024 tokens)",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=0,
            process=Process.sequential
        )

        result = crew.kickoff()
        return str(result)

    def run_review(self, code: str, lang: str = "python", log_dir: str = "cookbook/63_parallel_code_review/logs-spl") -> str:
        """Run the parallel code review - simulates CALL PARALLEL"""

        try:
            logger.info(f"[parallel_code_review] starting 3-way parallel review | lang={lang} review_model={self.review_model}")

            # CALL PARALLEL - run the three workflow functions concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                style_future = executor.submit(style_review, code, lang, self.review_model, log_dir)
                security_future = executor.submit(security_audit, code, lang, self.review_model, log_dir)
                test_future = executor.submit(test_generator, code, lang, self.review_model, log_dir)

                # Wait for all to complete
                style_fb = style_future.result()
                sec_fb = security_future.result()
                test_fb = test_future.result()

            logger.info('[parallel_code_review] parallel checks complete — merging into report')

            # GENERATE merge_reviews with OUTPUT BUDGET 1024 TOKENS
            report = self.merge_reviews(style_fb, sec_fb, test_fb)

            logger.info(f"[parallel_code_review] done | report_len={len(report)}")

            return report

        except Exception as e:
            error_msg = str(e).lower()
            if "model unavailable" in error_msg or "model not found" in error_msg:
                logger.error(f"[parallel_code_review] model unavailable: {self.review_model}")
                return "[ERROR] Model unavailable."
            elif "budget exceeded" in error_msg or "token" in error_msg or "limit" in error_msg:
                logger.warning("[parallel_code_review] token budget exceeded during merge")
                return report if 'report' in locals() else "[ERROR] Budget exceeded"
            else:
                logger.error(f"[parallel_code_review] unexpected error: {e}")
                return f"[ERROR] {str(e)}"

def parallel_code_review(code: str, lang: str = "python", review_model: str = "gemma4", log_dir: str = "cookbook/63_parallel_code_review/logs-spl") -> str:
    """Main entry point for parallel code review"""
    reviewer = ParallelCodeReview(review_model=review_model)
    return reviewer.run_review(code, lang, log_dir)

if __name__ == "__main__":
    # Usage example matching SPL INPUT defaults
    sample_code = "def add(a, b): return a - b"

    result = parallel_code_review(
        code=sample_code,
        lang="python",
        review_model="gemma4",
        log_dir="cookbook/63_parallel_code_review/logs-spl"
    )

    print("=== PARALLEL CODE REVIEW RESULT ===")
    print(result)
```
LLM calls: 3  Latency: 255166ms
Log:     /home/papagame/.spl/logs/llm_splc-claude_cli-20260420-184708.md
(spl123) papagame@papa-game:~/projects/digital-duck/SPL.py$ 
