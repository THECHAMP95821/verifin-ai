from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .filings import Filings
    from .financial_facts import FinancialFacts


class Company(Base):
    __tablename__ = "companies"

    __table_args__ = (
        Index("idx_companies_ticker", "ticker"),
    )

    cik: Mapped[str] = mapped_column(String(10), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    filings: Mapped[list[Filings]] = relationship(
        "Filings",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    financial_facts: Mapped[list[FinancialFacts]] = relationship(
        "FinancialFacts",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )