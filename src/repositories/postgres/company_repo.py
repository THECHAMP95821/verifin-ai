from fastapi import Depends
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Company
from core.deps import get_db_session
from collections.abc import Sequence


class CompanyRepo():
    def __init__(self, session: AsyncSession = Depends(get_db_session)) -> Sequence[str]:
        self.session = session

    async def bulk_insert_ignore_duplicates(self, data: list[dict]):
        stmt = insert(Company).values(data).on_conflict_do_nothing(
            index_elements=["cik"]  # Unique constraint / PK column
        ).returning(Column("cik"))
        res = await self.session.execute(stmt)
        print(res)
        inserted_ciks = res.scalars().all()
        return inserted_ciks