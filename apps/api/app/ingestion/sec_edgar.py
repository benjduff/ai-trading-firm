import hashlib
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.schemas.evidence import Evidence, EvidenceSource

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{document}"

DEFAULT_FORMS = ("10-K", "10-Q", "8-K")
EXCERPT_MAX_CHARS = 4000
INTER_REQUEST_DELAY_SECONDS = 0.2


class SecEdgarError(Exception):
    pass


class TickerNotFoundError(SecEdgarError):
    pass


@dataclass
class FilingMeta:
    form: str
    filing_date: str
    accession_number: str
    primary_document: str


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": settings.sec_edgar_user_agent},
        timeout=20.0,
    )


def lookup_cik(ticker: str, client: httpx.Client) -> str:
    response = client.get(TICKERS_URL)
    response.raise_for_status()
    for entry in response.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"])
    raise TickerNotFoundError(f"No SEC EDGAR CIK found for ticker {ticker!r}")


def list_filings(
    cik: str,
    client: httpx.Client,
    forms: tuple = DEFAULT_FORMS,
    limit_per_form: int = 2,
) -> list:
    url = SUBMISSIONS_URL.format(cik=cik)
    response = client.get(url)
    response.raise_for_status()
    recent = response.json()["filings"]["recent"]

    counts = {form: 0 for form in forms}
    filings = []
    for i, form in enumerate(recent["form"]):
        if form not in forms or counts[form] >= limit_per_form:
            continue
        filings.append(
            FilingMeta(
                form=form,
                filing_date=recent["filingDate"][i],
                accession_number=recent["accessionNumber"][i],
                primary_document=recent["primaryDocument"][i],
            )
        )
        counts[form] += 1
        if all(count >= limit_per_form for count in counts.values()):
            break
    return filings


def build_filing_url(cik: str, filing: FilingMeta) -> str:
    accession_no_dashes = filing.accession_number.replace("-", "")
    return ARCHIVES_URL.format(
        cik=cik.lstrip("0") or "0",
        accession_no_dashes=accession_no_dashes,
        document=filing.primary_document,
    )


def extract_excerpt(html_bytes: bytes) -> str:
    soup = BeautifulSoup(html_bytes, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        tag.decompose()
    for tag in soup.find_all(True):
        if tag.name and ":" in tag.name:
            tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:EXCERPT_MAX_CHARS]


def fetch_filing_evidence(
    ticker: str,
    forms: tuple = DEFAULT_FORMS,
    limit_per_form: int = 2,
) -> list:
    ticker = ticker.upper()
    ingested_at = datetime.now(timezone.utc)

    with _client() as client:
        cik = lookup_cik(ticker, client)
        time.sleep(INTER_REQUEST_DELAY_SECONDS)

        filings = list_filings(cik, client, forms=forms, limit_per_form=limit_per_form)

        evidence_list = []
        for filing in filings:
            time.sleep(INTER_REQUEST_DELAY_SECONDS)
            url = build_filing_url(cik, filing)
            doc_response = client.get(url)
            doc_response.raise_for_status()
            raw = doc_response.content

            published_at = datetime.strptime(
                filing.filing_date, "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)

            evidence_list.append(
                Evidence(
                    ticker=ticker,
                    source=EvidenceSource.SEC_EDGAR,
                    source_url=url,
                    document_hash=hashlib.sha256(raw).hexdigest(),
                    claim=f"{filing.form} filed on {filing.filing_date}",
                    excerpt=extract_excerpt(raw),
                    published_at=published_at,
                    ingested_at=ingested_at,
                )
            )

        return evidence_list
