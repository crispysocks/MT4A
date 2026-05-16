import re
from pathlib import Path
from typing import Optional, List


class SoulManager:
    def __init__(self, souls_dir: str = "souls"):
        self.souls_dir = Path(souls_dir)
        self._active_soul: Optional[dict] = None
        self.current_role: Optional[str] = None

    def load(self, role: str) -> None:
        soul_path = self.souls_dir / role / "SOUL.md"
        if not soul_path.exists():
            self._active_soul = None
            self.current_role = None
            return

        text = soul_path.read_text(encoding="utf-8")
        meta, body = self._parse_frontmatter(text)

        self._active_soul = {
            "name": meta.get("name", role),
            "role": meta.get("role", role),
            "tools": meta.get("tools", []),
            "system_prompt": body.strip(),
        }
        self.current_role = meta.get("role", role)

    def unload(self) -> None:
        self._active_soul = None
        self.current_role = None

    def is_active(self) -> bool:
        return self._active_soul is not None

    def get_system_prompt(self) -> str:
        if not self._active_soul:
            return "You are a helpful assistant."
        return self._active_soul["system_prompt"]

    def get_tools(self) -> List[str]:
        if not self._active_soul:
            return []
        return self._active_soul.get("tools", [])

    def _parse_frontmatter(self, text: str) -> tuple:
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text

        meta = {}
        for line in match.group(1).strip().splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                meta[key] = value

        return meta, match.group(2).strip()
