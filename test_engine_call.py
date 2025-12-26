import subprocess
import json
import sys

cmd = [
    sys.executable,
    "engine/engine_main.py",
    "--query",
    "test from gui"
]

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)

if result.stdout:
    data = json.loads(result.stdout)
    print("Parsed answer:", data["answer"])
