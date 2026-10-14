SEC_HEADERS = {
    "User-Agent": "VeriFinAI Research parv@verifin.ai",
    "Accept-Encoding": "gzip, deflate",
}

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{padded_cik}.json"

ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{raw_cik}/{cik_without_hyphens}/{primary_document}"
