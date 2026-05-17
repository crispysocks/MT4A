import json
import os
import re
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

from app.agent.soul import SoulManager

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
                text = f.read_text(encoding="utf-8")
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


# Tool registration is centralized in app/agent/tools/__init__.py
# Edit souls/tool_config.yaml to control which tools each agent role can use.
from app.agent.tools import registry

soul_manager = SoulManager()

SYSTEM = f"""You are a coding agent at {WORKDIR}. Use tools to solve tasks.
Use TodoWrite for short checklists. Use load_skill for specialized knowledge.
Skills: {SKILLS.descriptions()}"""


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def agent_loop(messages: list, stream_callback=None, system_prompt: str = None):
    """
    Agent 主循环
    
    Args:
        messages: 消息列表（会被原地修改）
        stream_callback: 可选回调，每次 LLM 输出 token 时调用 callback(text: str)
        system_prompt: 可选，覆盖 soul_manager 的 system prompt
    """
    if system_prompt is None:
        system_prompt = soul_manager.get_system_prompt()
    active_system_prompt = system_prompt
    rounds_without_todo = 0
    while True:
        microcompact(messages)
        if estimate_tokens(messages) > TOKEN_THRESHOLD:
            print("[auto-compact triggered]")
            messages[:] = auto_compact(messages)

        if stream_callback:
            # 流式模式（支持工具调用）
            response_stream = client.messages.create(
                model=MODEL, system=active_system_prompt, messages=messages,
                tools=registry.list(allowed_tools=soul_manager.get_tools() or None),
                max_tokens=8000, stream=True,
            )
            
            # 构建完整的 content blocks
            content_blocks = []
            current_block = None
            stop_reason = None
            
            for event in response_stream:
                if event.type == "content_block_start":
                    block_type = getattr(event.content_block, 'type', None) if event.content_block else None
                    if block_type == "text":
                        current_block = {"type": "text", "text": ""}
                    elif block_type == "tool_use":
                        current_block = {
                            "type": "tool_use",
                            "id": getattr(event.content_block, 'id', ''),
                            "name": getattr(event.content_block, 'name', ''),
                            "input": "",
                        }
                    elif block_type == "thinking":
                        current_block = {"type": "thinking", "text": ""}
                    else:
                        current_block = None
                    if current_block:
                        content_blocks.append(current_block)
                
                elif event.type == "content_block_delta":
                    if current_block and current_block["type"] == "text":
                        try:
                            text = event.delta.text
                            current_block["text"] += text
                            stream_callback(text, "content")
                        except AttributeError:
                            pass
                    elif current_block and current_block["type"] == "thinking":
                        try:
                            text = event.delta.thinking
                            current_block["text"] += text
                            stream_callback(text, "thinking")
                        except AttributeError:
                            pass
                    elif current_block and current_block["type"] == "tool_use":
                        try:
                            current_block["input"] += event.delta.partial_json
                        except AttributeError:
                            pass
                
                elif event.type == "content_block_stop":
                    current_block = None
                
                elif event.type == "message_delta":
                    if hasattr(event, 'delta') and event.delta:
                        stop_reason = getattr(event.delta, 'stop_reason', None)
            
            # 如果没有收到 stop_reason，默认为 end_turn
            if stop_reason is None:
                stop_reason = "end_turn"
            
            # 解析 tool_use 的 input JSON
            for block in content_blocks:
                if block["type"] == "tool_use":
                    try:
                        block["input"] = json.loads(block["input"]) if block["input"] else {}
                    except (json.JSONDecodeError, TypeError):
                        block["input"] = {}
            
            # 如果没有 content blocks，添加空文本块
            if not content_blocks:
                content_blocks = [{"type": "text", "text": ""}]
            
            # 添加到消息历史
            messages.append({"role": "assistant", "content": content_blocks})
            
            # 如果没有工具调用，直接返回
            if stop_reason != "tool_use":
                return
            
            # 处理工具调用
            results = []
            used_todo = False
            manual_compress = False
            for block in content_blocks:
                if block["type"] == "tool_use":
                    if block["name"] == "compress":
                        manual_compress = True
                    try:
                        handler = registry.get_handler(block["name"])
                        output = handler(**block["input"])
                    except Exception as e:
                        output = f"Error: {e}"
                    print(f"> {block['name']}:")
                    print(str(output)[:200])
                    results.append({"type": "tool_result", "tool_use_id": block["id"], "content": str(output)})
                    if block["name"] == "TodoWrite":
                        used_todo = True
            
            rounds_without_todo = 0 if used_todo else rounds_without_todo + 1
            if TODO.has_open_items() and rounds_without_todo >= 3:
                results.append({"type": "text", "text": "<reminder>Update your todos.</reminder>"})
            
            messages.append({"role": "user", "content": results})
            
            if manual_compress:
                print("[manual compact]")
                messages[:] = auto_compact(messages)
                return
        else:
            # 同步模式（原有逻辑）
            response = client.messages.create(
                model=MODEL, system=active_system_prompt, messages=messages,
                tools=registry.list(allowed_tools=soul_manager.get_tools() or None),
                max_tokens=8000,
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