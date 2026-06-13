"""Railway multi-service start wrapper (web + Band workers)."""
import os
import sys

SERVICE = os.environ.get("SERVICE_TYPE", "web")
PORT = os.environ.get("PORT", "5000")

COMMANDS = {
    "coordinator": [sys.executable, "agents/coordinator.py"],
    "intake": [sys.executable, "agents/intake.py"],
    "verification": [sys.executable, "agents/verification.py"],
    "resource": [sys.executable, "agents/resource.py"],
    "web": [
        "gunicorn",
        "-w",
        "4",
        "-b",
        f"0.0.0.0:{PORT}",
        "--timeout",
        "120",
        "--keep-alive",
        "5",
        "--max-requests",
        "1000",
        "frontend.app:app",
    ],
}

cmd = COMMANDS.get(SERVICE, COMMANDS["web"])
os.execvp(cmd[0], cmd)
