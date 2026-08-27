#!/usr/bin/env python3
"""
ai_autofix.py
Feature branch only. Reads the quality-gate error log, sends it plus the
current .tf files to Gemini, and asks for corrected file content. Writes
the corrected files back to disk. The workflow (bash) commits/pushes them.
"""
import glob
import json
import sys
from pathlib import Path
from gemini_client import call_gemini

EXPLANATION_FILE = Path("ai_fix_explanation.md")

def main() -> int:
    error_log_path = Path(sys.argv[1] if len(sys.argv) > 1 else "quality_gate_error.log")
    error_log = error_log_path.read_text(errors="ignore") if error_log_path.exists() else "No error log found."

    tf_files = sorted(glob.glob("*.tf"))
    files_section = "\n".join(
        f"### {path}\n{Path(path).read_text()}" for path in tf_files
    )

    prompt = f"""You are fixing a Terraform error inside an automated CI pipeline
running on a non-production feature branch. Your fix will be pushed as a
commit and will still go through normal PR review and a Trivy/tflint/tfsec
security gate before it can ever reach main - so a real human reviews it
before it can affect production.

Here is the error output from the pipeline:
--- ERROR LOG ---
{error_log}

Here are the current .tf files in the repo:
--- FILES ---
{files_section}

Fix ONLY what is necessary to resolve the error above. Do not change
resource names, variable names, or add new resources/features. Keep the
fix minimal and safe.

Respond with ONLY valid JSON, no markdown fences, no extra text, matching
exactly this schema:
{{
  "explanation": "one or two sentences describing the root cause and the fix",
  "files": [ {{ "path": "main.tf", "content": "FULL corrected file content" }} ]
}}

Only include files you actually changed. If you cannot confidently
determine a fix, return {{"explanation": "unable to determine a safe fix", "files": []}}.
"""

    raw = call_gemini(prompt, max_output_tokens=4096)
    if not raw:
        print("AI call failed or returned nothing.", file=sys.stderr)
        return 1

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"Could not parse AI response as JSON: {e}", file=sys.stderr)
        print(raw, file=sys.stderr)
        return 1

    explanation = parsed.get("explanation", "No explanation provided.")
    files = parsed.get("files", [])

    if not files:
        print(f"AI could not determine a safe fix: {explanation}", file=sys.stderr)
        return 1

    for entry in files:
        path = entry.get("path")
        content = entry.get("content")
        if not path or content is None:
            continue
        Path(path).write_text(content)
        print(f"Updated: {path}")

    EXPLANATION_FILE.write_text(f"AI auto-fix applied [ai-autofix]\n\n{explanation}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
