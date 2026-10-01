from fastapi import Depends
from sqlalchemy import Column, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Company
from src.core.deps import get_db_session
from collections.abc import Sequence


class CompanyRepo:
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def bulk_insert_ignore_duplicates(self, data: list[dict]):
        stmt = insert(Company).values(data).on_conflict_do_nothing(
            index_elements=["cik"]
        ).returning(Column("cik"))
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_companies_data(self) -> Sequence[Company]:
        stmt = select(Company)
        res = await self.session.execute(stmt)
        return res.scalars().all()