from app.rag.router import KnowledgeRouter

ROLE_BASES = {
    "student": ["company/public", "business", "policy"],
    "employee": ["company/public", "company/internal", "business", "policy"],
    "guest": ["company/public", "business", "policy"],
}


class FakeSoulManager:
    def __init__(self, role=None):
        self.current_role = role

    def is_active(self):
        return self.current_role is not None


def test_knowledge_router_for_guest():
    soul = FakeSoulManager("guest")
    router = KnowledgeRouter(soul, ROLE_BASES)
    bases = router.get_allowed_bases()
    assert "company/public" in bases
    assert "business" in bases
    assert "policy" in bases
    assert "company/internal" not in bases


def test_knowledge_router_for_employee():
    soul = FakeSoulManager("employee")
    router = KnowledgeRouter(soul, ROLE_BASES)
    bases = router.get_allowed_bases()
    assert "company/internal" in bases


def test_knowledge_router_no_soul():
    soul = FakeSoulManager(None)
    router = KnowledgeRouter(soul, ROLE_BASES)
    bases = router.get_allowed_bases()
    assert "company/public" in bases
    assert "company/internal" not in bases
