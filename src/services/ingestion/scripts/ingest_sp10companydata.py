import requests

from repositories.postgres.company_repo import CompanyRepo
from src.core.postgres import AsyncSessionFactory, engine
import asyncio
from src.scripts.script_runtime import run_script
import logfire



async def run_pipeline():
    async with run_script(service_name="sp10-seed-pipeline") as ctx:
      company_repo = CompanyRepo(ctx.session)
      url = "https://www.sec.gov/files/company_tickers_exchange.json"

      payload = {}
      headers = {
        'User-Agent': 'Jane Doe janedoe@example.com'
      }

      response = requests.request("GET", url, headers=headers, data=payload)

      res_json = response.json()
      company_data=[]
      cnt=0
      for company in res_json["data"][:20]:
        if company[3]!="Nasdaq":
          continue

        if cnt==10:
          break
        cnt+=1
        company_data.append({
          "cik": str(company[0]).zfill(10),
          "name": company[1],
          "ticker": company[2],
          "exchange": company[3],
        })

      with logfire.span("Postgres Bulk Upsert Operation"):
        print(company_data)
        inserted_ciks = await company_repo.bulk_insert_ignore_duplicates( company_data)
        # await ctx.session.commit()
        print(f"\n================ VERIFICATION ================")
        print(f"Total Sent to Postgres : {len(company_data)}")
        print(f"Rows Actually Inserted : {len(inserted_ciks)}")
        print(f"Newly Inserted CIKs    : {inserted_ciks}")
        logfire.info(f"Total Sent to Postgres : {len(company_data)}")
        logfire.info(f"Rows Actually Inserted : {len(inserted_ciks)}")
        logfire.info(f"Newly Inserted CIKs    : {inserted_ciks}")




async def main():
  try:
    await run_pipeline()
  finally:
    # Close connection pools cleanly so script can exit
    await engine.dispose()


if __name__ == "__main__":
  asyncio.run(main())





