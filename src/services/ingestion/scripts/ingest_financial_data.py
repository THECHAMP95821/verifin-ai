import asyncio
from typing import Any
from edgar import Company, set_identity
import logfire
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from enums.filing_types import FilingType
from repositories.postgres.company_repo import CompanyRepo
from scripts.script_runtime import run_script
from services.ingestion.quantitative_ingestion import QuantitativeIngestion
from src.core.postgres import engine


async def ingest_filing_worker(
    sem: asyncio.Semaphore,
    session_factory: async_sessionmaker[AsyncSession],
    filing: Any,
    filing_type: FilingType,
    period: str,
    ticker: str,
    fiscal_year: int,
) -> int:
  """Throttled worker: Checks out a dedicated session from the pool and ingests the filing."""
  async with sem:
    with logfire.span(
        f"Ingesting {ticker} {filing_type.value} ({period}) -"
        f" {filing.accession_number}"
    ):
      try:
        async with session_factory() as session:
          async with session.begin():
            ingestion = QuantitativeIngestion(
                session=session,
                filing=filing,
                filing_type=filing_type,
                period=period,
                fiscal_year=fiscal_year,
            )
            inserted_count = await ingestion.ingest()
            return inserted_count or 0
      except Exception as e:
        logfire.error(
            f"Failed ingesting {filing.accession_number} for {ticker}: {e}"
        )
        return 0


async def process_company_filings(
    comp_record: Any,
    session_factory: async_sessionmaker[AsyncSession],
    sem: asyncio.Semaphore,
    tg: asyncio.TaskGroup,
    tasks: list[asyncio.Task[int]],
) -> None:
  """Fetches filings chronologically and schedules them in the TaskGroup."""
  ticker = comp_record.ticker

  try:
    comp = await asyncio.to_thread(Company, ticker)
  except Exception as e:
    logfire.error(f"Failed to initialize Company({ticker}): {e}")
    return

  for fiscal_year in range(2024, 2027):
    # Rule: 2026 has no 10-K filings; only fetch 10-Q
    forms = ["10-Q"] if fiscal_year == 2026 else ["10-K", "10-Q"]

    for form in forms:
      try:
        filings = await asyncio.to_thread(
            comp.get_filings,
            year=fiscal_year,
            form=form,
            sort_by="filing_date",
        )
      except Exception as e:
        logfire.warning(
            f"Error fetching {form} for {ticker} in {fiscal_year}: {e}"
        )
        continue

      if not filings:
        continue

      if form == "10-K":
        # Newest 10-K for the fiscal year
        tasks.append(
            tg.create_task(
                ingest_filing_worker(
                    sem=sem,
                    session_factory=session_factory,
                    filing=filings[0],
                    filing_type=FilingType.TEN_K,
                    period="FY",
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                )
            )
        )
      else:
        # Filings are newest -> oldest: slice top 3 and reverse to get chronological [Q1, Q2, Q3]
        chronological_10qs = list(reversed(filings[:3]))

        for idx, filing in enumerate(chronological_10qs, start=1):
          period = f"Q{idx}"
          tasks.append(
              tg.create_task(
                  ingest_filing_worker(
                      sem=sem,
                      session_factory=session_factory,
                      filing=filing,
                      filing_type=FilingType.TEN_Q,
                      period=period,
                      ticker=ticker,
                      fiscal_year=fiscal_year,
                  )
              )
          )


async def run_pipeline():
  # Pool is 20 + 10 overflow. 12 workers utilize capacity without exhausting pool connections
  sem = asyncio.Semaphore(12)
  session_factory = async_sessionmaker(engine, expire_on_commit=False)

  async with run_script(service_name="extract-financial-data-3") as ctx:
    with logfire.span("Fetching target companies"):
      companies = await CompanyRepo(ctx.session).get_companies_data()
      logfire.info(f"Targeting {len(companies)} companies")

    tasks: list[asyncio.Task[int]] = []

    async with asyncio.TaskGroup() as tg:
      for company in companies:
        await process_company_filings(
            comp_record=company,
            session_factory=session_factory,
            sem=sem,
            tg=tg,
            tasks=tasks,
        )

    total_facts = sum(t.result() for t in tasks if not t.cancelled())
    logfire.info(
        f"Pipeline complete. Ingested {total_facts} facts across {len(tasks)}"
        " filings."
    )


async def main():
  set_identity("parvmalhotra1006@gmail.com")
  try:
    await run_pipeline()
  finally:
    await engine.dispose()


if __name__ == "__main__":
  asyncio.run(main())