"""dbman — 统一数据库操作工具（自然语言入口）"""
import os
import yaml
from pathlib import Path
from anthropic import Anthropic

from app.agent.tools.nl2sql import NL2SQLEngine, SchemaExtractor, extract_sql
from app.agent.tools.sql_validator import SQLValidator, SQLExecutor

_nl2sql_engine = None
_tables_config = None


def _load_tables_config() -> dict:
    global _tables_config
    if _tables_config is None:
        config_path = Path("souls/nl2sql/tables.yaml")
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                _tables_config = yaml.safe_load(f) or {}
        else:
            _tables_config = {}
    return _tables_config


def _get_engine() -> NL2SQLEngine:
    global _nl2sql_engine
    if _nl2sql_engine is None:
        client = Anthropic(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_AUTH_TOKEN"),
        )
        schema = SchemaExtractor().extract()
        soul_path = Path("souls/nl2sql/SOUL.md")
        soul_template = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
        if soul_template.startswith("---"):
            parts = soul_template.split("---", 2)
            if len(parts) >= 3:
                soul_template = parts[2].strip()
        _nl2sql_engine = NL2SQLEngine(client, schema, soul_template)
    return _nl2sql_engine


def dbman(nl: str) -> str:
    """数据库操作工具 — 接收自然语言，生成SQL并执行"""
    try:
        from app.agent.core import soul_manager
        role = soul_manager.current_role or "employee"

        tables_config = _load_tables_config()
        allowed_tables = tables_config.get(role, [])
        if not allowed_tables:
            return "错误：当前角色无权访问任何数据库表。"

        engine = _get_engine()
        sql = engine.generate_sql(nl, role, allowed_tables)

        if not sql or not any(kw in sql.upper() for kw in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
            return "未能理解您的查询，请换一种说法。"

        validator = SQLValidator(allowed_tables)
        validation = validator.validate(sql)
        if not validation.is_valid:
            return f"操作被拒绝：{validation.error}"

        executor = SQLExecutor()
        result = executor.execute(validation.sql)

        if "error" in result:
            return f"执行出错：{result['error']}"

        if "rows" in result:
            if result["count"] == 0:
                return "未找到相关数据。"
            return f"查询到 {result['count']} 条结果：\n```json\n{_format_json(result['rows'])}\n```"

        if "affected_rows" in result:
            return f"操作成功，影响 {result['affected_rows']} 行。"

        return "操作完成。"

    except Exception as e:
        return f"错误：{e}"


def _format_json(rows: list, max_rows: int = 10) -> str:
    import json
    display = rows[:max_rows]
    output = json.dumps(display, default=str, ensure_ascii=False, indent=2)
    if len(rows) > max_rows:
        output += f"\n... 仅显示前 {max_rows} 条，共 {len(rows)} 条"
    return output