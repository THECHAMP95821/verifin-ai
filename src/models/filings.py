from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .financial_facts import FinancialFacts


class Filings(Base):
    __tablename__ = "filings"

    __table_args__ = (
        UniqueConstraint(
            "cik",
            "filing_type",
            "fiscal_year",
            "filing_url",
            name="uq_filing_entry",
        ),
        Index(
            "idx_filings_lookup",
            "cik",
            "fiscal_year",
            "filing_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cik: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("companies.cik", ondelete="CASCADE"),
        nullable=False,
    )
    filing_type: Mapped[str] = mapped_column(String(10), nullable=False)
    filing_url: Mapped[str] = mapped_column(Text, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    company: Mapped[Company] = relationship(
        "Company",
        back_populates="filings",
    )
    financial_facts: Mapped[list[FinancialFacts]] = relationship(
        "FinancialFacts",
        back_populates="filings",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )