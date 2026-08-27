"""
gemini_client.py
Small stdlib-only helper for calling the Gemini API from CI.
"""
import json
import os
import urllib.request
import urllib.error

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

def call_gemini(prompt: str, max_output_tokens: int = 1024) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set.", flush=True)
        return None

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_output_tokens},
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Gemini API call failed: {e}", flush=True)
        return None

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None
