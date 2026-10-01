from fastapi import Depends
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from core.deps import get_db_session
from models import FinancialFacts


class FinancialFactsRepo():

    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def bulk_upsert(self, data: list[dict]):
        if not data:
            return []

        stmt = insert(FinancialFacts).values(data)

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[
                "filing_id", "concept_id", "human_label", "dimension_member", "raw_concept"
            ],
            set_={
                "value": stmt.excluded.value,
                # "updated_at": func.now(),
            },
        ).returning(FinancialFacts.id)

        res = await self.session.execute(upsert_stmt)
        return res.scalars().all()
