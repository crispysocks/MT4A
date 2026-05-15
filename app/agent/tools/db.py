from app.db.connection import engine
from sqlmodel import Session, select
from app.db.models import Course, Event, Registration
import json
from typing import Optional, Dict, Any


def _parse_conditions(conditions: Optional[str]) -> Dict[str, Any]:
    """Parse conditions JSON string into a dict."""
    if not conditions:
        return {}
    try:
        return json.loads(conditions)
    except json.JSONDecodeError:
        return {}


def _apply_conditions(stmt, model, conditions: Dict[str, Any]):
    """Apply field equality filters to a SQLModel select statement."""
    for field, value in conditions.items():
        if hasattr(model, field):
            stmt = stmt.where(getattr(model, field) == value)
    return stmt


def db_query(operation: str, table: str, conditions: str = None, data: dict = None) -> str:
    """Query or modify database.

    Args:
        operation: One of "select", "insert", "update", "delete"
        table: One of "courses", "events", "registrations"
        conditions: JSON string of field=value filters, e.g. '{"status": "active"}'
        data: Dict of field values for insert/update operations
    """
    try:
        with Session(engine) as session:
            model_map = {
                "courses": Course,
                "events": Event,
                "registrations": Registration,
            }
            model = model_map.get(table)
            if not model:
                return f"Error: Unknown table '{table}'. Available: {', '.join(model_map.keys())}"

            op = operation.lower()

            if op == "select":
                stmt = select(model)
                conds = _parse_conditions(conditions)
                stmt = _apply_conditions(stmt, model, conds)
                results = session.exec(stmt).all()
                if not results:
                    return "No records found."
                return json.dumps([r.model_dump() for r in results], default=str, ensure_ascii=False)

            elif op == "insert":
                if not data:
                    return "Error: 'data' parameter required for insert operation"
                obj = model(**data)
                session.add(obj)
                session.commit()
                session.refresh(obj)
                return f"Inserted {table} record with id={obj.id}"

            elif op == "update":
                if not data:
                    return "Error: 'data' parameter required for update operation"
                conds = _parse_conditions(conditions)
                if not conds:
                    return "Error: 'conditions' parameter required to identify which records to update"
                stmt = select(model)
                stmt = _apply_conditions(stmt, model, conds)
                results = session.exec(stmt).all()
                if not results:
                    return "No records found matching conditions"
                updated_count = 0
                for obj in results:
                    for field, value in data.items():
                        if hasattr(obj, field):
                            setattr(obj, field, value)
                    updated_count += 1
                session.commit()
                return f"Updated {updated_count} {table} record(s)"

            elif op == "delete":
                conds = _parse_conditions(conditions)
                if not conds:
                    return "Error: 'conditions' parameter required to identify which records to delete"
                stmt = select(model)
                stmt = _apply_conditions(stmt, model, conds)
                results = session.exec(stmt).all()
                if not results:
                    return "No records found matching conditions"
                deleted_count = 0
                for obj in results:
                    session.delete(obj)
                    deleted_count += 1
                session.commit()
                return f"Deleted {deleted_count} {table} record(s)"

            else:
                return f"Error: Unknown operation '{operation}'. Available: select, insert, update, delete"

    except Exception as e:
        return f"Error: {e}"
