from __future__ import annotations

import uuid
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ParentChunks(Base):
    __tablename__ = "parent_chunks"

    __table_args__ = (
        Index("idx_parent_chunks_filing_id", "filing_id"),
        Index("idx_parent_chunks_cik", "cik"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    cik: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("companies.cik", ondelete="CASCADE", name="fk_parents_company"),
        nullable=False,
    )
    filing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("filings.id", ondelete="CASCADE", name="fk_parents_filing"),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    section_name: Mapped[str] = mapped_column(String(100), nullable=False)

    text_content: Mapped[str] = mapped_column(Text, nullable=False)