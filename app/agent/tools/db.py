from app.db.connection import engine
from sqlmodel import Session
from app.db.models import Course, Event, Registration
import json

def db_query(operation: str, table: str, conditions: str = None, data: dict = None) -> str:
    """Query or modify database via natural language parameters."""
    try:
        with Session(engine) as session:
            if table == "courses":
                model = Course
            elif table == "events":
                model = Event
            elif table == "registrations":
                model = Registration
            else:
                return f"Error: Unknown table '{table}'"

            if operation.lower() == "select":
                results = session.select(model).all()
                return json.dumps([r.model_dump() for r in results], default=str, ensure_ascii=False)
            elif operation.lower() == "insert":
                obj = model(**data) if data else model()
                session.add(obj)
                session.commit()
                return f"Inserted: {obj.id}"
            elif operation.lower() == "update":
                return "Update operation not yet implemented"
            else:
                return f"Error: Unknown operation '{operation}'"
    except Exception as e:
        return f"Error: {e}"