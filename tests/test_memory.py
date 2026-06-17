from citrus.memory.base import MemoryItem
from citrus.memory.noop import NoopMemoryStore
from citrus.memory.service import MemoryService


def test_memory_service_uses_store_boundary() -> None:
    service = MemoryService(NoopMemoryStore())

    assert service.retrieve_for_task("testing") == []
    assert service.propose_updates([]) == []


def test_memory_item_has_scope_and_content() -> None:
    item = MemoryItem(scope="project", content="Use pytest")

    assert item.scope == "project"
    assert item.content == "Use pytest"
