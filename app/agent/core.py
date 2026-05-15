import json
import os
import re
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

WORKDIR = Path.cwd()
MODEL = os.environ.get("MODEL_ID", "qwen3.6-plus")

client = Anthropic(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_AUTH_TOKEN"),
)

SKILLS_DIR = WORKDIR / "skills"
TRANSCRIPT_DIR = WORKDIR / ".transcripts"
TOKEN_THRESHOLD = 100_000


# ---------------------------------------------------------------------------
# TodoWrite (s03)
# ---------------------------------------------------------------------------
class TodoManager:
    def __init__(self):
        self.items = []

    def update(self, items: list) -> str:
        validated, ip = [], 0
        for i, item in enumerate(items):
            content = str(item.get("content", "")).strip()
            status = str(item.get("status", "pending")).lower()
            af = str(item.get("activeForm", "")).strip()
            if not content:
                raise ValueError(f"Item {i}: content required")
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Item {i}: invalid status '{status}'")
            if not af:
                raise ValueError(f"Item {i}: activeForm required")
            if status == "in_progress":
                ip += 1
            validated.append({"content": content, "status": status, "activeForm": af})
        if len(validated) > 20:
            raise ValueError("Max 20 todos")
        if ip > 1:
            raise ValueError("Only one in_progress allowed")
        self.items = validated
        return self.render()

    def render(self) -> str:
        if not self.items:
            return "No todos."
        lines = []
        for item in self.items:
            m = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}.get(item["status"], "[?]")
            suffix = f" <- {item['activeForm']}" if item["status"] == "in_progress" else ""
            lines.append(f"{m} {item['content']}{suffix}")
        done = sum(1 for t in self.items if t["status"] == "completed")
        lines.append(f"\n({done}/{len(self.items)} completed)")
        return "\n".join(lines)

    def has_open_items(self) -> bool:
        return any(item.get("status") != "completed" for item in self.items)


TODO = TodoManager()


# ---------------------------------------------------------------------------
# Skill loading (s05)
# ---------------------------------------------------------------------------
class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills = {}
        if skills_dir.exists():
            for f in sorted(skills_dir.rglob("SKILL.md")):
                text = f.read_text()
                match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
                meta, body = {}, text
                if match:
                    for line in match.group(1).strip().splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meta[k.strip()] = v.strip()
                    body = match.group(2).strip()
                name = meta.get("name", f.parent.name)
                self.skills[name] = {"meta": meta, "body": body}

    def descriptions(self) -> str:
        if not self.skills:
            return "(no skills)"
        return "\n".join(f"  - {n}: {s['meta'].get('description', '-')}" for n, s in self.skills.items())

    def load(self, name: str) -> str:
        s = self.skills.get(name)
        if not s:
            return f"Error: Unknown skill '{name}'. Available: {', '.join(self.skills.keys())}"
        return f"<skill name=\"{name}\">\n{s['body']}\n</skill>"


SKILLS = SkillLoader(SKILLS_DIR)


# ---------------------------------------------------------------------------
# Context compression (s06)
# ---------------------------------------------------------------------------
def estimate_tokens(messages: list) -> int:
    return len(json.dumps(messages, default=str)) // 4


def microcompact(messages: list):
    indices = []
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    indices.append(part)
    if len(indices) <= 3:
        return
    for part in indices[:-3]:
        if isinstance(part.get("content"), str) and len(part["content"]) > 100:
            part["content"] = "[cleared]"


def auto_compact(messages: list) -> list:
    TRANSCRIPT_DIR.mkdir(exist_ok=True)
    path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.jsonl"
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    conv_text = json.dumps(messages, default=str)[-80000:]
    resp = client.messages.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"Summarize for continuity:\n{conv_text}"}],
        max_tokens=2000,
    )
    summary = resp.content[0].text
    return [
        {"role": "user", "content": f"[Compressed. Transcript: {path}]\n{summary}"},
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------
def todo_write_handler(items: list) -> str:
    return TODO.update(items)


def load_skill_handler(name: str) -> str:
    return SKILLS.load(name)


def compress_handler() -> str:
    return "Compressing..."


# Import and register additional tools
from app.agent.tools import registry

registry.register(
    "TodoWrite",
    todo_write_handler,
    {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}, "activeForm": {"type": "string"}}, "required": ["content", "status", "activeForm"]}}}, "required": ["items"]},
    "Update task tracking list."
)
registry.register(
    "load_skill",
    load_skill_handler,
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    "Load specialized knowledge by name."
)
registry.register(
    "compress",
    compress_handler,
    {"type": "object", "properties": {}},
    "Manually compress conversation context."
)

SYSTEM = f"""You are a coding agent at {WORKDIR}. Use tools to solve tasks.
Use TodoWrite for short checklists. Use load_skill for specialized knowledge.
Skills: {SKILLS.descriptions()}"""


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def agent_loop(messages: list, stream_callback=None):
    """
    Agent 主循环
    
    Args:
        messages: 消息列表（会被原地修改）
        stream_callback: 可选回调，每次 LLM 输出 token 时调用 callback(text: str)
    """
    rounds_without_todo = 0
    while True:
        microcompact(messages)
        if estimate_tokens(messages) > TOKEN_THRESHOLD:
            print("[auto-compact triggered]")
            messages[:] = auto_compact(messages)

        if stream_callback:
            # 流式模式
            response_stream = client.messages.create(
                model=MODEL, system=SYSTEM, messages=messages,
                tools=registry.list(), max_tokens=8000, stream=True,
            )
            
            collected_text = []
            for event in response_stream:
                if event.type == "content_block_delta":
                    try:
                        text = event.delta.text
                        collected_text.append(text)
                        stream_callback(text)
                    except AttributeError:
                        pass
            
            # 构建完整响应对象
            full_text = "".join(collected_text)
            messages.append({"role": "assistant", "content": full_text})
            
            # 流式模式下不处理工具调用（简化版）
            return
        else:
            # 同步模式（原有逻辑）
            response = client.messages.create(
                model=MODEL, system=SYSTEM, messages=messages,
                tools=registry.list(), max_tokens=8000,
            )
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "tool_use":
                return

            results = []
            used_todo = False
            manual_compress = False
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "compress":
                        manual_compress = True
                    try:
                        handler = registry.get_handler(block.name)
                        output = handler(**block.input)
                    except Exception as e:
                        output = f"Error: {e}"
                    print(f"> {block.name}:")
                    print(str(output)[:200])
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
                    if block.name == "TodoWrite":
                        used_todo = True

            rounds_without_todo = 0 if used_todo else rounds_without_todo + 1
            if TODO.has_open_items() and rounds_without_todo >= 3:
                results.append({"type": "text", "text": "<reminder>Update your todos.</reminder>"})

            messages.append({"role": "user", "content": results})

            if manual_compress:
                print("[manual compact]")
                messages[:] = auto_compact(messages)
                return