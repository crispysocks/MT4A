from typing import List, Optional

ROLE_KNOWLEDGE_BASES = {
    "student": ["company/public", "business", "policy"],
    "employee": ["company/public", "company/internal", "business", "policy"],
    "guest": ["company/public", "business", "policy"],
}


class KnowledgeRouter:
    def __init__(self, soul_manager, role_bases: dict = None):
        self.soul_manager = soul_manager
        self.role_bases = role_bases or ROLE_KNOWLEDGE_BASES

    def get_allowed_bases(self) -> List[str]:
        if self.soul_manager.is_active():
            role = self.soul_manager.current_role
            return self.role_bases.get(role, self.role_bases.get("guest", []))
        return self.role_bases.get("guest", [])

    def build_where_filter(self) -> Optional[dict]:
        allowed = self.get_allowed_bases()
        return {"source": {"$in": allowed}} if allowed else None


# Global instance, initialized on app startup
knowledge_router: Optional[KnowledgeRouter] = None
