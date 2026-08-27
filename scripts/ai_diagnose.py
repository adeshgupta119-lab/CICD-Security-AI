#!/usr/bin/env python3
"""
ai_diagnose.py
Main branch / apply failures only. READ-ONLY - explains a likely root
cause, never writes or changes any code. Output goes into the GitHub
Actions job summary by the workflow.
"""
import sys
from pathlib import Path
from gemini_client import call_gemini

OUT_FILE = Path("diagnosis.md")

def main() -> None:
    error_log_path = Path(sys.argv[1] if len(sys.argv) > 1 else "error_log.txt")
    stage = sys.argv[2] if len(sys.argv) > 2 else "unknown stage"

    error_log = error_log_path.read_text(errors="ignore")[:8000] if error_log_path.exists() else "No error log found."

    prompt = f"""Terraform failed at the "{stage}" stage in a production CI/CD
pipeline, AFTER the change was already merged to main. You must NOT
propose a code diff or claim you fixed anything - this stage requires a
human to investigate, since it may involve real cloud resource state.
Just explain clearly, for an engineer who did not see the failure live,
what most likely went wrong and what they should check first.

Respond ONLY in this Markdown structure, no preamble:

## AI Diagnosis: {stage} failed

**Likely cause:** <1-2 sentences, best guess from the log>

**What to check first:**
- <bullet>
- <bullet>

**Note:** This is a read-only diagnosis. No code was changed automatically.

--- ERROR LOG ---
{error_log}
"""

    summary = call_gemini(prompt, max_output_tokens=700)

    if not summary:
        OUT_FILE.write_text(
            f"## AI Diagnosis: {stage} failed\n\n"
            f"_AI diagnosis call failed or no API key configured. Raw error log below._\n\n"
            f"```\n{error_log}\n```\n"
        )
    else:
        OUT_FILE.write_text(summary)

if __name__ == "__main__":
    main()
