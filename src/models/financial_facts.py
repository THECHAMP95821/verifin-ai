from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .filings import Filings
    from .standard_concepts import StandardConcepts


class FinancialFacts(Base):
    __tablename__ = "financial_facts"

    __table_args__ = (
        UniqueConstraint(
            "cik",
            "concept_key",
            "period",
            "dimension_member",
            "filing_id",
            name="uq_fact_coordinate",
        ),
        Index(
            "idx_facts_sandbox_query",
            "cik",
            "concept_key",
            "period",
            "dimension_member",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    concept_key: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("standard_concepts.concept_key"),
        nullable=False,
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

    statement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    dimension_member: Mapped[str] = mapped_column(String(255), nullable=False)
    value_usd_integer: Mapped[int] = mapped_column(BigInteger, nullable=False)
    decimals_exponent: Mapped[int] = mapped_column(Integer, nullable=False)
    balance: Mapped[str] = mapped_column(String(10), nullable=False)
    human_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    concept: Mapped[StandardConcepts] = relationship(
        "StandardConcepts",
        back_populates="financial_facts",
    )
    company: Mapped[Company] = relationship(
        "Company",
        back_populates="financial_facts",
    )
    filing: Mapped[Filings] = relationship(
        "Filings",
        back_populates="financial_facts",
    )