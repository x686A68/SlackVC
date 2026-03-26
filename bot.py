import os
import re
import ssl
import json
import certifi
import subprocess
import threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

load_dotenv()

CLAUDE_PATH = os.path.expanduser("~/.local/bin/claude")
APPROVED_TOOLS_PATH = os.path.join(os.path.dirname(__file__), "approved_tools.json")
SESSIONS_PATH = os.path.join(os.path.dirname(__file__), "sessions.json")

with open(os.path.join(os.path.dirname(__file__), "channels.json")) as f:
    CHANNEL_MAP: dict[str, str] = json.load(f)


def load_sessions() -> dict:
    try:
        with open(SESSIONS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

def save_sessions(s: dict):
    with open(SESSIONS_PATH, "w") as f:
        json.dump(s, f)

sessions: dict[str, str] = load_sessions()
pending_permissions: dict[str, dict] = {}

# Approved tools (persisted to disk)
def load_approved_tools() -> set:
    try:
        with open(APPROVED_TOOLS_PATH) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_approved_tools(tools: set):
    with open(APPROVED_TOOLS_PATH, "w") as f:
        json.dump(list(tools), f)

approved_tools: set = load_approved_tools()

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)



def approve_permissions(denials: list[dict]):
    global approved_tools
    for d in denials:
        tool = d["tool_name"]
        if tool not in approved_tools:
            approved_tools.add(tool)
            print(f"[permissions] permanently allowed: {tool}")
    save_approved_tools(approved_tools)


def format_denials(denials: list[dict]) -> str:
    lines = []
    for d in denials:
        tool = d["tool_name"]
        inp = d.get("tool_input", {})
        if tool == "Write":
            detail = f"write `{inp.get('file_path', '?')}`"
        elif tool in ("Edit", "MultiEdit"):
            detail = f"edit `{inp.get('file_path', '?')}`"
        elif tool == "Bash":
            detail = f"run `{str(inp.get('command', '?'))[:80]}`"
        else:
            detail = str(inp)[:80]
        lines.append(f"• *{tool}*: {detail}")
    return "\n".join(lines)


def run_claude(prompt: str, channel_id: str, work_dir: str, say, depth: int = 0) -> str:
    if depth > 3:
        return "Too many retries due to permission issues."

    cmd = [CLAUDE_PATH, "-p", prompt, "--output-format", "json"]
    session_id = sessions.get(channel_id)
    if session_id:
        cmd += ["--resume", session_id]
    cmd += ["--dangerously-skip-permissions"]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=work_dir, timeout=300
    )

    raw = result.stdout.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw or result.stderr.strip() or "(no output)"

    if "session_id" in data:
        sessions[channel_id] = data["session_id"]
        save_sessions(sessions)

    denials = data.get("permission_denials", [])
    print(f"[denials] {denials}")
    if denials:
        denial_text = format_denials(denials)
        event = threading.Event()
        pending_permissions[channel_id] = {"event": event, "response": "n", "denials": denials}

        say(
            f"⚠️ Claude is requesting permissions:\n{denial_text}\n\n"
            f"@ me with `y` to approve (remembered permanently) or `n` to deny."
        )
        event.wait(timeout=120)
        state = pending_permissions.pop(channel_id, {})

        if state.get("response") == "y":
            approve_permissions(denials)
            say("✅ Approved, retrying...")
            return run_claude(prompt, channel_id, work_dir, say, depth + 1)
        else:
            return "❌ Permission denied, operation cancelled."

    return data.get("result", raw)


def send_long_message(say, text: str):
    for i in range(0, len(text), 2800):
        say(text[i : i + 2800])


@app.event("app_mention")
def handle_mention(event, say):
    channel_id = event["channel"]
    prompt = event.get("text", "").split(">", 1)[-1].strip()

    if not prompt:
        return

    # Permission reply
    if prompt.lower() in ("y", "n", "yes", "no") and channel_id in pending_permissions:
        state = pending_permissions[channel_id]
        state["response"] = "y" if prompt.lower() in ("y", "yes") else "n"
        state["event"].set()
        return

    if channel_id not in CHANNEL_MAP:
        say("This channel has no project configured. Please add it to channels.json.")
        return

    if prompt.lower() in ("new", "new session", "reset"):
        sessions.pop(channel_id, None)
        save_sessions(sessions)
        say("New session started.")
        return

    work_dir = CHANNEL_MAP[channel_id]
    print(f"[{channel_id}] {prompt[:80]}")

    output = run_claude(prompt, channel_id, work_dir, say)
    send_long_message(say, output)


if __name__ == "__main__":
    print(f"Bot started. Configured channels: {list(CHANNEL_MAP.keys())}")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
