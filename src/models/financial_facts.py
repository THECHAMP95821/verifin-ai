from __future__ import annotations

from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FinancialFacts(Base):
    __tablename__ = "financial_facts"

    __table_args__ = (
        UniqueConstraint( "filing_id", "concept_id", "human_label", "dimension_member", "raw_concept",
                          name="unique_cik_fiscal_year_period",
                          postgresql_nulls_not_distinct=True),
        Index("idx_facts_sandbox_query", "cik", "fiscal_year", "period", "concept_id"),
        Index("idx_facts_filing_id", "filing_id", "concept_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("standard_concepts.id"), nullable=False
    )
    cik: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("companies.cik", ondelete="CASCADE"),
        nullable=False,
    )
    filing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("filings.id", ondelete="CASCADE"),
        nullable=False,
    )
    raw_concept: Mapped[str | None] = mapped_column(String(255), nullable=True)
    statement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    dimension_member: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(28, 4), nullable=False)
    human_label: Mapped[str | None] = mapped_column(Text, nullable=True)
