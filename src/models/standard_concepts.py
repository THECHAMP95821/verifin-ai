from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StandardConcepts(Base):
    __tablename__ = "standard_concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
