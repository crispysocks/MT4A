"""NL2SQL 引擎 — 自然语言转SQL"""
import re
import os


class SchemaExtractor:
    """从 SQLModel metadata 动态提取表schema"""

    def extract(self) -> str:
        from sqlmodel import SQLModel
        from app.db.models import (
            Course, Event, Registration, User, Lead, LeadFollowUp,
            DailyReport, Complaint, Organization, StudentGrade,
            LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning,
        )

        lines = []
        for table_name, table in SQLModel.metadata.tables.items():
            if table_name.startswith("_"):
                continue
            cols = []
            for col in table.columns:
                parts = [col.name, str(col.type)]
                if col.primary_key:
                    parts.append("PK")
                if col.foreign_keys:
                    fk = ", ".join(fk.target_fullname for fk in col.foreign_keys)
                    parts.append(f"FK→{fk}")
                if not col.nullable:
                    parts.append("NOT NULL")
                cols.append(" ".join(parts))
            lines.append(f"Table: {table_name}")
            lines.append(f"Columns: {', '.join(cols)}")
            lines.append("")

        return "\n".join(lines).strip()


def extract_sql(text: str) -> str:
    """从LLM响应中提取纯SQL（去除markdown标记和解释文字）"""
    match = re.search(r'```sql\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r'```\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    for line in text.split("\n"):
        line_stripped = line.strip().upper()
        if any(line_stripped.startswith(kw) for kw in sql_keywords):
            return line.strip()

    return text.strip()


class NL2SQLEngine:
    def __init__(self, llm_client, schema_context: str, soul_template: str):
        self.llm = llm_client
        self.schema_context = schema_context
        self.soul_template = soul_template

    def generate_sql(self, natural_query: str, role: str, allowed_tables: list[str]) -> str:
        system_prompt = self._build_system_prompt(role, allowed_tables)

        response = self.llm.messages.create(
            model=os.environ.get("MODEL_ID", "qwen3.6-plus"),
            system=system_prompt,
            messages=[{"role": "user", "content": natural_query}],
            max_tokens=int(os.getenv("NL2SQL_MAX_TOKENS", "2000")),
        )
        for block in response.content:
            if hasattr(block, "text") and block.text:
                return extract_sql(block.text)
        return ""

    def _build_system_prompt(self, role: str, allowed_tables: list[str]) -> str:
        prompt = self.soul_template
        prompt += f"\n\n## 数据库Schema\n{self.schema_context}"
        prompt += f"\n\n## 可访问表\n你只能操作以下表: {', '.join(allowed_tables)}"
        prompt += f"\n\n## 当前角色\n{role}"
        return prompt