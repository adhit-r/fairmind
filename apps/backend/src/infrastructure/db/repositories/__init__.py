"""Database repository adapters with lazy compatibility exports."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .ai_bom_repository import AIBOMRepository

__all__ = ["AIBOMRepository"]


def __getattr__(name: str) -> Any:
    if name == "AIBOMRepository":
        from .ai_bom_repository import AIBOMRepository

        return AIBOMRepository
    raise AttributeError(name)
