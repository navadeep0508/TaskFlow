"""
Quick diagnostic to test Groq API key and model availability.
Run: .\venv\Scripts\python scratch\test_groq.py
"""
import os
import sys

# Manually load .env since we're not in Flask context
from pathlib import Path
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"'))

api_key = os.environ.get("GROQ_API_KEY", "")
print(f"API Key found: {'YES — ' + api_key[:12] + '...' if api_key else 'NO'}")

if not api_key:
    print("ERROR: GROQ_API_KEY not set in .env")
    sys.exit(1)

try:
    from groq import Groq
    client = Groq(api_key=api_key)
    print("Groq client created successfully.")
except ImportError:
    print("ERROR: groq package not installed. Run: .\\venv\\Scripts\\pip install groq")
    sys.exit(1)
except Exception as e:
    print(f"ERROR creating client: {e}")
    sys.exit(1)

# Test with a simple prompt
models_to_try = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

for model in models_to_try:
    print(f"\nTesting model: {model} ...")
    try:
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": 'Return this exact JSON: {"ok": true}'}],
            model=model,
            temperature=0,
            max_tokens=32,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        print(f"  ✅ SUCCESS — Response: {content.strip()}")
        break
    except Exception as e:
        print(f"  ❌ FAILED — {e}")
