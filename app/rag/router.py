from typing import List, Optional

ROLE_KNOWLEDGE_BASES = {
    "student": ["public", "business", "policy"],
    "employee": ["public", "internal", "business", "policy"],
    "guest": ["public", "business", "policy"],
}


class KnowledgeRouter:
    def __init__(self, soul_manager, role_bases: dict = None):
        self.soul_manager = soul_manager
        self.role_bases = role_bases or ROLE_KNOWLEDGE_BASES
        self.faq_roles: list[str] = []

    def get_allowed_kbs(self) -> List[str]:
        if self.soul_manager.is_active():
            role = self.soul_manager.current_role
            return self.role_bases.get(role, self.role_bases.get("guest", []))
        return self.role_bases.get("guest", [])


knowledge_router: Optional[KnowledgeRouter] = None
