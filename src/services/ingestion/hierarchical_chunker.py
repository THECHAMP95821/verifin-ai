import asyncio
from models import Filings
from schemas.qualitative_ingestion import SectionMarkdown, ParentChunksDTO, ChildChunkDTO
from services.ingestion.tokenizer import Tokenizer
import logfire


class HierarchicalChunker:
    def __init__(self,
                 tokenizer: Tokenizer = Tokenizer(),
                 parent_target_tokens = 1200,
                 child_target_tokens = 250,
                 child_overlap_tokens = 50
    ):
        if child_overlap_tokens >= child_target_tokens:
            raise ValueError(
                f"child_overlap_tokens ({child_overlap_tokens}) must be strictly less"
                f" than child_target_tokens ({child_target_tokens})."
            )
        if child_target_tokens > parent_target_tokens:
            raise ValueError(
                f"child_target_tokens ({child_target_tokens}) cannot exceed"
                f" parent_target_tokens ({parent_target_tokens})."
            )
        self.tokenizer = tokenizer
        self.parent_target_tokens = parent_target_tokens
        self.child_target_tokens = child_target_tokens
        self.child_overlap_tokens = child_overlap_tokens

    async def async_chunk_document(self, sections: list[SectionMarkdown], filing: Filings, ticker: str):
        return await asyncio.to_thread(
            self.chuck_document,
            sections,
            filing,
            ticker
        )

    def chuck_document(self, sections: list[SectionMarkdown], filing: Filings, ticker: str) -> tuple[list[ParentChunksDTO], list[list[ChildChunkDTO]]]:
        logfire.info(f"Chunking document {filing.accession_number}")
        parent_chunks: list[ParentChunksDTO] = []
        child_chunks: list[list[ChildChunkDTO]] = []

        for section in sections:
            md_text = section.markdown_text
            sec_tokens = self.tokenizer.encode(md_text)
            total_tokens = len(sec_tokens)

            for i in range(0, total_tokens, self.parent_target_tokens):
                j = min(total_tokens, i + self.parent_target_tokens)
                tokens = sec_tokens[i:j]
                content = self.tokenizer.decode(tokens)
                parent = ParentChunksDTO(
                    cik = filing.cik,
                    filing_id= filing.id,
                    section_name=section.header_path,
                    markdown_text=content,
                    header_path=section.header_path,
                )
                children  = self.collect_child_chunks(parent, filing, ticker)
                parent_chunks.append(parent)
                child_chunks.append(children)
        return parent_chunks, child_chunks

    def collect_child_chunks(self, parent: ParentChunksDTO, filing: Filings, ticker: str) -> list[ChildChunkDTO]:
        md_text = parent.markdown_text
        tokens = self.tokenizer.encode(md_text)
        total_tokens = len(tokens)
        children: list[ChildChunkDTO] = []
        for i in range(0, total_tokens, self.child_target_tokens - self.child_overlap_tokens):
            j = min(total_tokens, i + self.child_target_tokens)
            slice_tokens = tokens[i:j]
            content = self.tokenizer.decode(slice_tokens)
            text_payload = f"[{ticker} | {filing.filing_type} | {parent.header_path}] " + content
            children.append(ChildChunkDTO(
                ticker=ticker,
                filing=filing,
                text_payload=text_payload
            ))
        return children

