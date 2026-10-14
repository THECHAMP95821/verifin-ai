# scripts/run_batch_ingestion.py
import asyncio
import logfire
import time
from sqlalchemy import select
from core.postgres import AsyncSessionFactory, engine
from core.qdrant import qdrant_client
from models import Company, Filings
from services.ingestion.qualitative_ingestion import QualitativeIngestion
from src.core.config import settings


async def run_batch_pipeline() -> None:
    with logfire.span("QUALITATIVE INGESTION"):
        logfire.info("Initializing persistent pipeline singletons...")

        try:
            async with AsyncSessionFactory() as session:
                # 1. FETCH ALL FILINGS TO PROCESS
                stmt = (
                    select(Filings, Company.ticker)
                    .join(Company, Filings.cik == Company.cik)
                    .order_by(Filings.id.asc())
                )
                result = await session.execute(stmt)
                filing_records = result.all()

                # Detach records from the session so rollbacks never expire them
                session.expunge_all()

                total_records = len(filing_records)
                logfire.info(
                    f"Retrieved {total_records} documents from database for ingestion."
                )

                if total_records == 0:
                    logfire.warning("No filings found to process. Exiting.")
                    return

                pipeline = QualitativeIngestion(
                    qdrant_client=qdrant_client,
                    session=session,
                )

                success_count = 0
                failure_count = 0

                # 2. PROCESS EACH FILING
                for idx, (filing, ticker) in enumerate(filing_records, start=1):
                    # Cache primitives before try block to prevent lazy-load failures
                    acc_no = str(filing.accession_number)
                    f_type = str(filing.filing_type)

                    start_time = time.perf_counter()
                    logfire.info(
                        f"[{idx}/{total_records}] Starting: {ticker} | {f_type} | Acc: {acc_no}"
                    )

                    try:
                        stats = await pipeline.ingest_document(
                            filing=filing, ticker=ticker
                        )

                        # Commit PostgreSQL parent chunk transaction
                        await session.commit()
                        session.expunge_all()

                        elapsed = time.perf_counter() - start_time
                        parents_count = (
                            stats["parents_stored"] if stats else 0
                        )
                        children_count = (
                            stats["children_stored"] if stats else 0
                        )

                        logfire.info(
                            f"[{idx}/{total_records}] Successfully ingested {acc_no} "
                            f"in {elapsed:.2f}s (Parents: {parents_count}, Children: {children_count})"
                        )
                        success_count += 1

                    except Exception as err:
                        # Transaction rollback on failure
                        await session.rollback()
                        session.expunge_all()
                        failure_count += 1

                        # Uses plain string acc_no, avoiding MissingGreenlet
                        logfire.error(
                            f"[{idx}/{total_records}] FAILED to ingest {acc_no}: {err}",
                            exc_info=True,
                        )
                        logfire.warning(
                            "Transaction rolled back. Continuing to next filing..."
                        )

                logfire.info(
                    f"Batch run completed! Total: {total_records} | Succeeded: {success_count} | Failed: {failure_count}"
                )

        finally:
            # 3. CLEAN RESOURCE DISPOSAL
            logfire.info("Closing open client connections and engine pools...")
            await qdrant_client.close()
            await engine.dispose()


if __name__ == "__main__":
    logfire.configure(
        token=settings.LOGFIRE_TOKEN,
        service_name="QUALITATIVE INGESTION",
        send_to_logfire=True,
    )
    logfire.instrument_sqlalchemy(engine.sync_engine)
    asyncio.run(run_batch_pipeline())