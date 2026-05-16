"""SoulManager - 加载/解析/卸载 SOUL.md，组装 system prompt."""

import yaml
from pathlib import Path


class SoulManager:
    CONFIG_FILENAME = "tool_config.yaml"

    def __init__(self, souls_dir: str = "souls"):
        self._base_dir = Path(souls_dir)
        self._active_soul: dict | None = None
        self.current_role = None
        self._tool_config = self._load_tool_config()

    # ------------------------------------------------------------------
    # Tool config
    # ------------------------------------------------------------------
    def _load_tool_config(self) -> dict:
        config_path = self._base_dir / self.CONFIG_FILENAME
        if not config_path.exists():
            print(f"[WARN] Tool config not found: {config_path}")
            return {}
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # ------------------------------------------------------------------
    # Load / unload
    # ------------------------------------------------------------------
    def load(self, role: str) -> None:
        soul_path = self._base_dir / role / "SOUL.md"
        if not soul_path.exists():
            print(f"[WARN] SOUL.md not found for role '{role}': {soul_path}")
            self._active_soul = None
            self.current_role = None
            return

        text = soul_path.read_text(encoding="utf-8")
        meta = self._parse_frontmatter(text)

        tools = self._tool_config.get(role, [])

        # Validate tools are registered
        from app.agent.tools.registry import registry
        all_registered = {t.name for t in registry._tools.values()}
        missing = set(tools) - all_registered
        if missing:
            print(f"[WARN] Soul '{role}' has unregistered tools: {missing}")
            tools = [t for t in tools if t in all_registered]

        self._active_soul = {
            "name": meta.get("name", role),
            "role": meta.get("role", role),
            "tools": tools,
            "system_prompt": meta.get("body", text).strip(),
        }
        self.current_role = role

    def unload(self) -> None:
        self._active_soul = None
        self.current_role = None

    def is_active(self) -> bool:
        return self._active_soul is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_system_prompt(self) -> str:
        if not self.is_active():
            return "You are a helpful assistant."

        prompt = self._active_soul["system_prompt"]
        tools = self._active_soul.get("tools", [])
        if not tools:
            return prompt

        from app.agent.tools.registry import registry
        descriptions = []
        for t in registry._tools.values():
            if t.name in tools:
                descriptions.append(f"- **{t.name}** — {t.description}")

        if descriptions:
            prompt += "\n\n## 可用工具\n" + "\n".join(descriptions)

        return prompt

    def get_tools(self) -> list[str]:
        if not self.is_active():
            return []
        return self._active_soul.get("tools", [])

    # ------------------------------------------------------------------
    # Frontmatter parser
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_frontmatter(text: str) -> dict:
        result = {"body": text}
        if not text.startswith("---"):
            return result

        parts = text.split("---", 2)
        if len(parts) < 3:
            return result

        frontmatter = parts[1].strip()
        body = parts[2].strip()
        result["body"] = body

        for line in frontmatter.split("\n"):
            line = line.strip()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                # Parse list: [item1, item2]
                value = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
            result[key] = value

        return result
