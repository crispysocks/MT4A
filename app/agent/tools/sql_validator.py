"""SQL 安全校验层 + 执行器"""
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    is_valid: bool
    sql: str
    error: str = ""


class SQLValidator:
    DANGEROUS_KEYWORDS = [
        "DROP", "ALTER", "TRUNCATE", "CREATE",
        "GRANT", "REVOKE", "EXEC", "EXECUTE",
    ]

    def __init__(self, allowed_tables: list[str], max_rows: int = 100):
        self.allowed_tables = set(t.lower() for t in allowed_tables)
        self.max_rows = max_rows

    def validate(self, sql: str) -> ValidationResult:
        sql_upper = sql.upper().strip()

        for kw in self.DANGEROUS_KEYWORDS:
            if re.search(r'\b' + kw + r'\b', sql_upper):
                return ValidationResult(False, sql, f"不允许使用 {kw} 操作")

        table = self._extract_table(sql_upper)
        if table and table not in self.allowed_tables:
            return ValidationResult(False, sql, f"无权访问表 {table}")

        if sql_upper.startswith("DELETE") and "WHERE" not in sql_upper:
            return ValidationResult(False, sql, "DELETE 语句必须包含 WHERE 条件")
        if sql_upper.startswith("UPDATE") and "WHERE" not in sql_upper:
            return ValidationResult(False, sql, "UPDATE 语句必须包含 WHERE 条件")

        if sql_upper.startswith("SELECT") and "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + f" LIMIT {self.max_rows}"

        return ValidationResult(True, sql)

    def _extract_table(self, sql_upper: str) -> str | None:
        patterns = [
            r'\bFROM\s+(\w+)',
            r'\bINTO\s+(\w+)',
            r'\bUPDATE\s+(\w+)',
            r'\bJOIN\s+(\w+)',
        ]
        for pattern in patterns:
            m = re.search(pattern, sql_upper)
            if m:
                return m.group(1).lower()
        return None