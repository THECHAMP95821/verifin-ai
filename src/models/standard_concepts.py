from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .financial_facts import FinancialFacts


class StandardConcepts(Base):
    __tablename__ = "standard_concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationships
    financial_facts: Mapped[list[FinancialFacts]] = relationship(
        "FinancialFacts",
        back_populates="concept",
    )