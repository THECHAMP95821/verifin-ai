import uuid
from dataclasses import dataclass

from models import Filings


@dataclass
class SectionMarkdown:
    markdown_text: str
    header_path: str

@dataclass
class ParentChunksDTO:
    cik: str
    filing_id: int
    section_name: str
    markdown_text: str
    header_path: str
    parent_id: uuid.UUID | None = None

@dataclass
class ChildChunkDTO:
    ticker: str
    filing: Filings
    text_payload: str
    embedding = list[float] | None
    parent_id: uuid.UUID | None = None
    child_id: uuid.UUID | None = None
