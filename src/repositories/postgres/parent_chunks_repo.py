
from fastapi import Depends
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db_session
from src.models import ParentChunks


class ParentChunksRepo:
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def bulk_insert(self, data: list[dict]):
        if not data:
            return []

        stmt = insert(ParentChunks).values(data).returning(Column("id"))
        res = await self.session.execute(stmt)
        return res.scalars().all()
