import crewai as cr
from crewai import tools

# Define tools
class StyleReviewTool(tools.Tool):
    name = "style_review"
    description = "Performs a style review on the given code."
    func = cr.llm_functions.get_function("00_style_review")

class SecurityAuditTool(tools.Tool):
    name = "security_audit"
    description = "Performs a security audit on the given code."
    func = cr.llm_functions.get_function("01_security_audit")

class TestGeneratorTool(tools.Tool):
    name = "test_generator"
    description = "Generates test cases for the given code."
    func = cr.llm_functions.get_function("02_test_generator")

# Define agent
class CodeReviewAgent(cr.Agent):
    name = "code_review_agent"
    tools = [StyleReviewTool(), SecurityAuditTool(), TestGeneratorTool()]
    default_tools = [StyleReviewTool(), SecurityAuditTool(), TestGeneratorTool()]

# Define the workflow
def parallel_code_review(code, lang="python", review_model="gemma3"):
    """
    Parallel code review workflow.
    """
    agent = CodeReviewAgent()

    style_fb = agent.call(
        "style_review",
        code=code,
        lang=lang,
        review_model=review_model,
        log_dir="cookbook/63_parallel_code_review/logs-spl"
    )

    sec_fb = agent.call(
        "security_audit",
        code=code,
        lang=lang,
        review_model=review_model,
        log_dir="cookbook/63_parallel_code_review/logs-spl"
    )

    tests = agent.call(
        "test_generator",
        code=code,
        lang=lang,
        review_model=review_model,
        log_dir="cookbook/63_parallel_code_review/logs-spl"
    )

    report = agent.call(
        "merge_reviews",
        style=style_fb,
        sec_audit=sec_fb,
        tests=tests
    )

    return report

# __main__ block for usage example
if __name__ == "__main__":
    code_snippet = "def add(a, b): return a - b"
    review_report = parallel_code_review(code_snippet)
    print(review_report)
