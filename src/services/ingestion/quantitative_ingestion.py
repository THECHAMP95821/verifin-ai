from typing import Any
import asyncio
from edgar.entity import EntityFiling
import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from enums.filing_types import FilingType

from enums.statement_types import StatementType
from repositories.postgres.filings_repo import FilingsRepo
from repositories.postgres.financial_facts_repo import FinancialFactsRepo
from repositories.postgres.standard_concepts_repo import StandardConceptsRepo


class QuantitativeIngestion:

    def __init__(self, session:AsyncSession, filing: EntityFiling, filing_type: FilingType, period: str|None, fiscal_year: int):
        self.session = session
        self.filing = filing
        self.filing_type = filing_type
        self.period = period
        self.fiscal_year = fiscal_year

    async def register_filing(self):
        filing_data = [
            {
                "accession_number": self.filing.accession_number,
                "period": self.period,
                "cik": str(self.filing.cik).zfill(10),
                "filing_type": self.filing_type,
                "filing_url": self.filing.filing_url,
                "fiscal_year": self.fiscal_year
            }
        ]
        with logfire.span(f"Registering filing data for {self.filing.accession_no}"):
            ids = await FilingsRepo(session=self.session).bulk_insert_ignore_duplicates(filing_data)
            logfire.info(f"FILING ID: {ids[0]}")
            return ids[0]


    async def ingest_dataframe(self, df: Any, filing_id: int, statement_type: StatementType):
        if df is None:
            return
        with logfire.span(f"Ingesting dataframe"):
            standard_concept = None
            standard_concepts = []
            financial_facts=[]

            for row in df.itertuples():
                if row.abstract is True:
                    continue
                if row.standard_concept is not None:
                    standard_concept = row.standard_concept
                    standard_concepts.append(standard_concept)
                financial_facts.append(
                    {
                        "concept_id": standard_concept,
                        "cik": str(self.filing.cik).zfill(10),
                        "filing_id": filing_id,
                        "statement_type": statement_type,
                        "period": self.period,
                        "dimension_member": row.dimension_member,
                        "fiscal_year": self.fiscal_year,
                        "value": float(row._4 * row.weight),
                        "human_label": row.label or None,
                        "raw_concept": row.concept,
                    }
                )
            concept_mapping = await StandardConceptsRepo(self.session).get_or_create_concept_map(standard_concepts)
            print(concept_mapping)
            for fact in financial_facts:
                fact["concept_id"] = concept_mapping.get(fact["concept_id"])
            fin_facts = await FinancialFactsRepo(self.session).bulk_upsert(financial_facts)
            logfire.info(f"{len(fin_facts)} FINANCIAL FACTS INSERTED IN DB")
            return len(fin_facts)




    async def ingest(self):
        filing_id: int = await self.register_filing()
        xbrl = self.filing.xbrl()
        statements = xbrl.statements

        inc_df = statements.income_statement(view="detailed").to_dataframe()
        bal_df = statements.balance_sheet(view="detailed").to_dataframe()
        cf_df = statements.cashflow_statement(view="detailed").to_dataframe()

        async with asyncio.TaskGroup() as tg:
            t_inc = tg.create_task(
                self.ingest_dataframe(inc_df, filing_id, StatementType.IncomeStatement)
            )
            t_bal = tg.create_task(
                self.ingest_dataframe(bal_df, filing_id, StatementType.BalanceSheet)
            )
            t_cf = tg.create_task(
                self.ingest_dataframe(cf_df, filing_id, StatementType.CashFlowStatement)
            )

        total_facts = t_inc.result() + t_bal.result() + t_cf.result()
        logfire.info(f"Ingested {total_facts} total facts across all statements")
        return total_facts
         