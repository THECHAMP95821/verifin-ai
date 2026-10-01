from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Filings(Base):
    __tablename__ = "filings"

    __table_args__ = (
        Index("idx_filings_lookup", "cik", "fiscal_year", "filing_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    accession_number: Mapped[str] = mapped_column(
        String(25), unique=True, nullable=False
    )

    period: Mapped[str] = mapped_column(String(20), nullable=False)

    cik: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("companies.cik", ondelete="CASCADE"),
        nullable=False,
    )
    filing_type: Mapped[str] = mapped_column(String(10), nullable=False)
    filing_url: Mapped[str] = mapped_column(Text, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
