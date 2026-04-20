import logging
from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelCodeReview:
    def __init__(self, review_model: str = "gemma3"):
        self.review_model = review_model

    def create_agents(self):
        """Create the three review agents plus merger"""

        style_reviewer = Agent(
            role="Code Style & Correctness Reviewer",
            goal="Analyze code for style issues, bugs, and correctness problems",
            backstory="You are an expert code reviewer focused on style guidelines, best practices, and correctness. You catch bugs, style violations, and suggest improvements.",
            verbose=True,
            allow_delegation=False
        )

        security_auditor = Agent(
            role="Security Auditor",
            goal="Identify security vulnerabilities and risks in code",
            backstory="You are a cybersecurity expert specializing in code security audits. You identify vulnerabilities, security anti-patterns, and potential attack vectors.",
            verbose=True,
            allow_delegation=False
        )

        test_generator = Agent(
            role="Test Case Generator",
            goal="Generate comprehensive test cases for the given code",
            backstory="You are a QA engineer expert at creating thorough test cases. You generate unit tests, edge cases, and integration tests to ensure code quality.",
            verbose=True,
            allow_delegation=False
        )

        report_merger = Agent(
            role="Senior Engineering Lead",
            goal="Consolidate multiple code review reports into actionable plans",
            backstory="You are a senior engineering lead with expertise in consolidating technical feedback into prioritized action items.",
            verbose=True,
            allow_delegation=False
        )

        return style_reviewer, security_auditor, test_generator, report_merger

    def create_tasks(self, code: str, lang: str, log_dir: str):
        """Create the review tasks"""

        style_reviewer, security_auditor, test_generator, report_merger = self.create_agents()

        style_task = Task(
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
            agent=style_reviewer
        )

        security_task = Task(
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
            agent=security_auditor
        )

        test_task = Task(
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
            agent=test_generator
        )

        merge_task = Task(
            description="""
            You are a senior engineering lead consolidating three independent code-review reports
            into a single, actionable plan.

            Style & Correctness Review:
            {style_review}

            Security Audit:
            {security_audit}

            Generated Test Cases:
            {test_cases}

            Produce a consolidated report with three sections:
            1. **Action Items** — numbered list of changes to make, CRITICAL first, then MODERATE, then LOW
            2. **Test Coverage** — paste the generated tests verbatim under a code block
            3. **Summary** — one paragraph overall assessment (is this code production-ready?)

            Keep the Action Items section under 150 words.
            """,
            expected_output="Consolidated code review report with prioritized action items, test coverage, and summary",
            agent=report_merger,
            context=[style_task, security_task, test_task]
        )

        return [style_task, security_task, test_task, merge_task]

    def run_review(self, code: str, lang: str = "python", log_dir: str = "cookbook/63_parallel_code_review/logs-spl") -> str:
        """Run the parallel code review"""

        try:
            logger.info(f"[parallel_code_review] starting 3-way parallel review | lang={lang} review_model={self.review_model}")

            # Create tasks
            tasks = self.create_tasks(code, lang, log_dir)

            # Create crew - the first 3 tasks can run independently, merge task waits for all
            crew = Crew(
                agents=[task.agent for task in tasks],
                tasks=tasks,
                verbose=2,
                process=Process.sequential
            )

            logger.info('[parallel_code_review] parallel checks complete — merging into report')

            # Execute the crew
            result = crew.kickoff()

            logger.info(f"[parallel_code_review] done | report_len={len(str(result))}")

            return str(result)

        except Exception as e:
            error_msg = str(e).lower()
            if "model unavailable" in error_msg or "model not found" in error_msg:
                logger.error(f"[parallel_code_review] model unavailable: {self.review_model}")
                return "[ERROR] Model unavailable."
            elif "budget exceeded" in error_msg or "token" in error_msg or "limit" in error_msg:
                logger.warning("[parallel_code_review] token budget exceeded during merge")
                return str(result) if 'result' in locals() else "[ERROR] Budget exceeded"
            else:
                logger.error(f"[parallel_code_review] unexpected error: {e}")
                return f"[ERROR] {str(e)}"

def parallel_code_review(code: str, lang: str = "python", review_model: str = "gemma3", log_dir: str = "cookbook/63_parallel_code_review/logs-spl") -> str:
    """Main entry point for parallel code review"""
    reviewer = ParallelCodeReview(review_model=review_model)
    return reviewer.run_review(code, lang, log_dir)

if __name__ == "__main__":
    # Usage example matching SPL INPUT defaults
    sample_code = "def add(a, b): return a - b"

    result = parallel_code_review(
        code=sample_code,
        lang="python",
        review_model="gemma3",
        log_dir="cookbook/63_parallel_code_review/logs-spl"
    )

    print("=== PARALLEL CODE REVIEW RESULT ===")
    print(result)
