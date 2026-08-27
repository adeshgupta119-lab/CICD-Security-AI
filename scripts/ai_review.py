#!/usr/bin/env python3
"""
ai_review.py
Feature-branch, plan succeeded. Sends the plan + Trivy/tfsec/tflint results to
Gemini and asks for a short risk summary to include in the PR body.
"""
from pathlib import Path
from gemini_client import call_gemini

PLAN_FILE = Path("plan_output.txt")
TRIVY_FILE = Path("trivy_results.json")
TFSEC_FILE = Path("tfsec_results.json")
TFLINT_FILE = Path("tflint_results.json")
OUT_FILE = Path("ai_summary.md")

def read_truncated(path: Path, limit: int) -> str:
    if not path.exists():
        return "Not available."
    return path.read_text(errors="ignore")[:limit]

def main() -> None:
    plan_excerpt = read_truncated(PLAN_FILE, 12000)
    trivy_excerpt = read_truncated(TRIVY_FILE, 4000)
    tfsec_excerpt = read_truncated(TFSEC_FILE, 4000)
    tflint_excerpt = read_truncated(TFLINT_FILE, 2000)

    prompt = f"""You are reviewing an infrastructure-as-code change before it is
applied to a real Azure environment. You will be shown a Terraform plan,
Trivy IaC scan results, tfsec results, and tflint results. Respond ONLY with concise
Markdown, no preamble, using this exact structure:

## AI Plan Review

**Risk level:** <Low | Medium | High>

**What this change does:** <2-3 sentences, plain language>

**Notable risks / things to double-check:**
- <bullet per concern, or "None identified" if truly none>

**Security findings summary (Trivy & tfsec):**
- <summarize findings in plain language, or "No issues found">

Do not invent resources or findings that are not present in the input. If
the plan only creates low-risk resources, say so plainly.

--- TERRAFORM PLAN ---
{plan_excerpt}

--- TRIVY RESULTS (JSON) ---
{trivy_excerpt}

--- TFSEC RESULTS (JSON) ---
{tfsec_excerpt}

--- TFLINT RESULTS (JSON) ---
{tflint_excerpt}
"""

    summary = call_gemini(prompt, max_output_tokens=1024)

    if not summary:
        OUT_FILE.write_text(
            "## AI Plan Review\n\n_AI review call failed or no API key configured._\n"
        )
    else:
        OUT_FILE.write_text(summary)

if __name__ == "__main__":
    main()
