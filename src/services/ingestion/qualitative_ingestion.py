import uuid

from aiolimiter import AsyncLimiter
from edgar import get_by_accession_number
import warnings

from constants.constants import SUBMISSIONS_URL, SEC_HEADERS, ARCHIVE_URL
from models import Filings
import sec_parser as sp
from sec_parser.semantic_tree.tree_node import TreeNode
from sec_parser.semantic_tree.semantic_tree import SemanticTree
from sec_parser.semantic_elements.semantic_elements import IntroductorySectionElement
from sec_parser import TableElement, AbstractSemanticElement, TextElement, SupplementaryText
from typing import cast
import httpx

from repositories.postgres.parent_chunks_repo import ParentChunksRepo
from repositories.qdrant.sec_qualitative_repo import SecQualitativeRepo
from schemas.qualitative_ingestion import SectionMarkdown, ParentChunksDTO, ChildChunkDTO
from services.ingestion.EmbeddingService import LocalEmbeddingService
from services.ingestion.hierarchical_chunker import HierarchicalChunker
from sqlalchemy.ext.asyncio import AsyncSession
from core.deps import get_db_session
from fastapi import Depends
import logfire


class QualitativeIngestion:
    def __init__(self, qdrant_client, session: AsyncSession = Depends(get_db_session)):
        self.client = httpx.AsyncClient(
            headers=SEC_HEADERS,
        )
        self.limiter = AsyncLimiter(max_rate=10, time_period=1)
        self.chunker_service = HierarchicalChunker()
        self.parent_chunks_repo = ParentChunksRepo(session=session)
        self.embedding_service = LocalEmbeddingService()
        self.sec_qualitative_repo = SecQualitativeRepo(qdrant_client)

    def get_markdown(
            self,
            tree: list[TreeNode] | TreeNode | SemanticTree | list[AbstractSemanticElement],
            ignored_types: tuple[type[AbstractSemanticElement], ...] = (TableElement, IntroductorySectionElement),
            _level: int = 0,
            _nodes: list[TreeNode] | None = None,
    ) -> str:
        if isinstance(tree, TreeNode):
            root_nodes = [tree]
        elif isinstance(tree, SemanticTree):
            root_nodes = list(tree)
        elif isinstance(tree, list) and tree:
            if all(isinstance(e, AbstractSemanticElement) for e in tree):
                elements = cast(list[AbstractSemanticElement], tree)
                root_nodes = [TreeNode(e) for e in elements]
            elif all(isinstance(e, TreeNode) for e in tree):
                root_nodes = cast(list[TreeNode], tree)
            else:
                msg = "All elements in the tree must be of type AbstractSemanticElement or TreeNode"
                raise TypeError(msg)
        else:
            msg = "Invalid type for 'tree'. Expected TreeNode, SemanticTree, list[AbstractSemanticElement], or list[TreeNode]"
            raise TypeError(msg)

        markdown = ""
        _nodes = _nodes if _nodes is not None else root_nodes
        for i, node in enumerate(_nodes):
            element = node.semantic_element
            if isinstance(element, ignored_types):
                continue
            contents = element.get_summary().strip()
            if "signature" in contents.lower():
                continue

            if isinstance(element, (TextElement, SupplementaryText)):
                heading_string = ""
            else:
                heading_string = '#' * (_level + 1) + ' '

            if contents:
                contents = heading_string + contents + '\n'

            markdown += contents

            markdown += self.get_markdown(
                root_nodes,
                ignored_types=ignored_types,
                _level=_level + 1,
                _nodes=node.children,
            )

        return markdown

    async def get_raw_html(self, filing: Filings) -> str:
        logfire.info(f"Getting raw html for acc_no {filing.accession_number}")
        cik = filing.cik
        async with self.limiter:
            submissions_res = await self.client.get(
                SUBMISSIONS_URL.format(padded_cik=cik)
            )
        submission_data = submissions_res.json()
        acc_nos = submission_data["filings"]["recent"]["accessionNumber"]
        primary_docs = submission_data["filings"]["recent"]["primaryDocument"]
        acc_no = filing.accession_number
        idx = acc_nos.index(acc_no)
        primary_doc = primary_docs[idx]
        raw_cik = cik.lstrip("0")
        cik_without_hyphens = "".join(acc_no.split('-'))
        async with self.limiter:
            archive_res = await self.client.get(
                ARCHIVE_URL.format(raw_cik=raw_cik, cik_without_hyphens=cik_without_hyphens,
                                   primary_document=primary_doc)
            )
        html = archive_res.text
        return html


    async def get_section_wise_markdown(self, filing: Filings) -> list[SectionMarkdown]:
        logfire.info(f"Getting section wise markdown for acc_no {filing.accession_number}")
        html=await self.get_raw_html(filing)
        parser = sp.Edgar10QParser()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Invalid section type for")
            elements: list = parser.parse(html)
        tree: sp.SemanticTree = sp.TreeBuilder().build(elements)
        section_wise_md = []
        for node in tree:
            section_name = node.semantic_element.get_summary()
            for child in node.children:
                title = child.semantic_element.get_summary()
                md = self.get_markdown(child)
                header_path = section_name + ' > ' + title
                section_wise_md.append(SectionMarkdown(
                    markdown_text=md,
                    header_path=header_path,
                ))
        return section_wise_md


    async def ingest_document(self, filing: Filings, ticker: str):
        section_wise_md = await self.get_section_wise_markdown(filing)
        parent_chunks, child_chunks = await self.chunker_service.async_chunk_document(
            sections=section_wise_md,
            filing=filing,
            ticker=ticker,

        )
        parent_chunk_data = []
        for pc in parent_chunks:
            parent_chunk_data.append({
                "cik": pc.cik,
                "filing_id": pc.filing_id,
                "section_name": pc.section_name,
                "text_content": pc.markdown_text
            })
        parent_ids = await self.parent_chunks_repo.bulk_insert(data=parent_chunk_data)
        flat_children = []
        for i, children in enumerate(child_chunks):
            p_id = parent_ids[i]
            for child in children:
                child.parent_id = p_id
                child.child_id = str(uuid.uuid4())
                flat_children.append(child)

        all_payloads = [c.text_payload for c in flat_children]
        embeddings = await self.embedding_service.embed_batch_async(
            texts=all_payloads,
        )

        for child, vector in zip(flat_children, embeddings):
            child.embedding = vector

        # 8. Upsert child points into Qdrant
        total_upserted = await self.sec_qualitative_repo.bulk_upsert_children(
            children=flat_children,
            batch_size=100,
        )
        return {
            "parents_stored": len(parent_chunks),
            "children_stored": total_upserted,
        }
