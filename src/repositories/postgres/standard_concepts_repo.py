from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.deps import get_db_session
from src.models.standard_concepts import StandardConcepts


class StandardConceptsRepo():

    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def get_or_create_concept_map(
            self, concept_keys: list[str]
    ) -> dict[str, int]:
        if not concept_keys:
            return {}

        unique_keys = list(set(concept_keys))

        insert_stmt = (
            insert(StandardConcepts)
            .values([{"concept_key": k} for k in unique_keys])
            .on_conflict_do_nothing(index_elements=["concept_key"])
        )
        await self.session.execute(insert_stmt)

        select_stmt = select(
            StandardConcepts.concept_key, StandardConcepts.id
        ).where(StandardConcepts.concept_key.in_(unique_keys))
        res = await self.session.execute(select_stmt)

        return {row.concept_key: row.id for row in res.all()}
