from select import select

from fastapi import Depends
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db_session
from src.models import Filings


class FilingsRepo:
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def bulk_insert_ignore_duplicates(self, data: list[dict]):
        if not data:
            return []

        stmt = insert(Filings).values(data)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["accession_number"],
            set_={
                "filing_url": stmt.excluded.filing_url,
                "period": stmt.excluded.period,
            },
        ).returning(Filings.id)

        res = await self.session.execute(upsert_stmt)
        return list(res.scalars().all())
