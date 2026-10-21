
"""
FixFlow RAG service.

- Preserves FixFlow's UUID-based tenant and document isolation.
- Uses the original Colab generation prompt and context structure.
- Keeps sources separate from the generated answer.
- Uses BAAI/bge-m3 embeddings and Groq generation.
"""

import logging
import os
import re
import uuid
from typing import Any

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from chunking import chunk_all
from cleaning import clean_text


load_dotenv()

logger = logging.getLogger("fixflow.rag")

QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "fixflow").strip()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

RAG_MODEL_NAME = os.getenv(
    "RAG_MODEL_NAME",
    "BAAI/bge-m3",
)

MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.45"))
TOP_K = int(os.getenv("RAG_TOP_K", "5"))
VECTOR_SIZE = 1024

INSUFFICIENT_EVIDENCE = (
    "The provided documents do not contain enough information "
    "to answer this question."
)

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError(
        "QDRANT_URL and QDRANT_API_KEY must be set in .env"
    )

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY must be set in .env")

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

groq = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)

_embedding_model = None


# ============================================================
# EMBEDDINGS
# ============================================================

def _get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        logger.info(
            "Loading embedding model: %s",
            RAG_MODEL_NAME,
        )
        _embedding_model = SentenceTransformer(
            RAG_MODEL_NAME
        )

    return _embedding_model


def _embed(texts: list[str]) -> list[list[float]]:
    vectors = _get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    return np.asarray(
        vectors,
        dtype=np.float32,
    ).tolist()


# ============================================================
# QDRANT COLLECTION
# ============================================================

def ensure_collection():
    collections = {
        item.name
        for item in qdrant.get_collections().collections
    }

    if QDRANT_COLLECTION not in collections:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )

    for field in ("tenant_id", "document_id"):
        try:
            qdrant.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True,
            )
        except Exception as exc:
            # Indexes may already exist.
            logger.debug(
                "Could not create payload index %s: %s",
                field,
                exc,
            )


# ============================================================
# DOCUMENT PREPARATION
# ============================================================

def make_document(
    content: bytes | str,
    filename: str,
    document_id: Any,
    tenant_id: Any,
):
    if isinstance(content, bytes):
        text = content.decode(
            "utf-8",
            errors="replace",
        )
    else:
        text = str(content)

    return {
        "text": clean_text(text),
        "metadata": {
            "source": filename,
            "filename": filename,
            "document_id": str(document_id),
            "tenant_id": str(tenant_id),
            "doc_code": filename,
            "synthetic": False,
        },
    }


# ============================================================
# DELETE A DOCUMENT'S VECTORS
# ============================================================

def delete_document_vectors(
    *,
    tenant_id,
    document_id,
):
    ensure_collection()

    qdrant.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(
                            value=str(tenant_id)
                        ),
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                            value=str(document_id)
                        ),
                    ),
                ]
            )
        ),
        wait=True,
    )


# ============================================================
# INDEX A DOCUMENT
# ============================================================

def index_document(
    *,
    tenant_id,
    document_id,
    filename,
    content,
) -> int:
    """
    Chunk, embed and index a tenant-owned document.
    Returns the number of indexed chunks.
    """

    document = make_document(
        content=content,
        filename=filename,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    chunks = chunk_all([document])

    if not chunks:
        delete_document_vectors(
            tenant_id=tenant_id,
            document_id=document_id,
        )
        return 0

    ensure_collection()

    valid_chunks = []

    for index, chunk in enumerate(chunks):
        text = str(chunk.get("text", "")).strip()

        if text:
            valid_chunks.append((index, chunk, text))

    if not valid_chunks:
        delete_document_vectors(
            tenant_id=tenant_id,
            document_id=document_id,
        )
        return 0

    vectors = _embed([
        text
        for _, _, text in valid_chunks
    ])

    points = []

    for (index, chunk, text), vector in zip(
        valid_chunks,
        vectors,
    ):
        metadata = dict(
            chunk.get("metadata") or {}
        )

        chunk_key = str(
            metadata.get("chunk_key")
            or f"{document_id}::{index}"
        )

        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{tenant_id}:{document_id}:{chunk_key}",
            )
        )

        payload = {
            **metadata,
            "tenant_id": str(tenant_id),
            "document_id": str(document_id),
            "source": (
                metadata.get("source")
                or filename
            ),
            "filename": filename,
            "doc_code": (
                metadata.get("doc_code")
                or metadata.get("source")
                or filename
            ),
            "section": (
                metadata.get("section")
                or "Overview"
            ),
            "text": text,
            "chunk_key": chunk_key,
        }

        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )

    # Delete only this document for this tenant.
    delete_document_vectors(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    qdrant.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points,
        wait=True,
    )

    logger.info(
        "Indexed %s chunks for document=%s, tenant=%s",
        len(points),
        document_id,
        tenant_id,
    )

    return len(points)


# ============================================================
# BUILD CONTEXT — ORIGINAL COLAB FORMAT
# ============================================================

def _build_context(hits: list[dict]) -> str:
    blocks = []

    for hit in hits:
        source_filename = (
            hit.get("source_filename")
            or hit.get("source")
            or hit.get("filename")
            or "Unknown source"
        )

        blocks.append(
            f"[Official Document: {source_filename}]\n"
            f"{hit.get('text', '')}"
        )

    return "\n\n---\n\n".join(blocks)


# Compatibility alias for the original Colab function name.
def build_context(results: list[dict]) -> str:
    return _build_context(results)


# ============================================================
# GENERATION PROMPT — ORIGINAL COLAB RULES
# ============================================================



def build_prompt(query: str, context: str, domain: str | None = None) -> str:
    domain_note = (
        f"Relevant support domain: {domain}\n"
        if domain
        else ""
    )

    return f"""
You are FixFlow, an AI customer-support assistant for Aurora Bank.

Your task is to answer the user's question using ONLY the
information contained in the retrieved document context below.

{domain_note}

STRICT RULES:

1. Use only facts explicitly supported by the provided context.
2. Do not use outside knowledge or assumptions.
3. Never invent or guess interest rates, fees, transaction limits,
   deadlines, phone numbers, email addresses, policies, or procedures.
4. If the context does not contain enough relevant information
   to answer the question, respond exactly with:
   "The provided documents do not contain enough information to answer this question."
5. Do not mention document names, filenames, document codes,
   section names, source names, or retrieval details.
6. Do not include citations, reference numbers, source links,
   or phrases such as "according to the document" in your answer.
   Sources are handled separately by the application.
7. Answer the user's actual question directly.
8. If the context provides a procedure, present the steps as a
   short numbered list in the correct order.
9. If the question is factual and simple, answer in 1–3 sentences.
10. If multiple retrieved passages provide relevant information,
    combine them only when they are consistent and supported.
11. If the retrieved passages conflict, do not choose one by guessing.
    State that the available information is insufficient to provide
    a reliable answer.
12. Do not claim that an action was completed. Explain what the user
    can do instead.
13. Keep the response concise, clear, and professional.
14. Use Markdown only when it improves readability.
15. Return only the answer text. Do not output headings such as
    "Answer", reasoning, source lists, or explanations of these rules.

RETRIEVED DOCUMENT CONTEXT:

<context>
{context}
</context>

USER QUESTION:

<question>
{query}
</question>

FINAL ANSWER:
""".strip()


# ============================================================
# RETRIEVAL — TENANT ISOLATION REQUIRED
# ============================================================

def _retrieve(
    query: str,
    tenant_id: Any,
    top_k: int,
) -> list[dict]:
    ensure_collection()

    query_vector = _embed([query])[0]

    response = qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(
                        value=str(tenant_id)
                    ),
                )
            ]
        ),
        limit=max(
            1,
            min(int(top_k), 20),
        ),
        with_payload=True,
        with_vectors=False,
    )

    hits = []

    for point in response.points:
        payload = point.payload or {}
        score = float(point.score or 0.0)

        if score < MIN_SCORE:
            continue

        text = str(payload.get("text") or "").strip()

        if not text:
            continue

        source = str(
            payload.get("source")
            or payload.get("filename")
            or "Unknown source"
        )

        hits.append({
            "score": score,
            "text": text,
            "source": source,
            "source_filename": source,
            "filename": str(
                payload.get("filename")
                or source
            ),
            "doc_code": payload.get("doc_code"),
            "section": (
                payload.get("section")
                or "Overview"
            ),
            "document_id": str(
                payload.get("document_id") or ""
            ),
            "chunk_key": str(
                payload.get("chunk_key") or ""
            ),
        })

    return hits


# ============================================================
# FALLBACK DETECTION
# ============================================================

def _is_insufficient(answer: str) -> bool:
    normalized = re.sub(
        r"\s+",
        " ",
        answer or "",
    ).strip().lower()

    fallback = re.sub(
        r"\s+",
        " ",
        INSUFFICIENT_EVIDENCE,
    ).strip().lower()

    return (
        not normalized
        or normalized == fallback
        or "insufficient_evidence" in normalized
    )


# ============================================================
# SOURCES — RETURN SEPARATELY FROM ANSWER
# ============================================================

def _citations_from_hits(
    hits: list[dict],
) -> list[dict]:
    citations = []
    seen = set()

    for hit in hits:
        key = (
            hit.get("document_id"),
            hit.get("section"),
            hit.get("source"),
        )

        if key in seen:
            continue

        seen.add(key)

        citations.append({
            "number": len(citations) + 1,
            "doc_code": hit.get("doc_code"),
            "source": hit.get("source"),
            "section": hit.get("section"),
            "document_id": hit.get("document_id"),
            "chunk_key": hit.get("chunk_key"),
            "score": hit.get("score"),
        })

    return citations


# ============================================================
# MAIN RAG FUNCTION — FIXFLOW API CONTRACT
# ============================================================

def answer_question(
    query: str,
    tenant_id: Any,
    top_k: int = TOP_K,
    **kwargs,
) -> dict:
    """
    Retrieve tenant-scoped context and generate an answer.

    Returns:
        {
            "answer": str,
            "insufficient_evidence": bool,
            "citations": list
        }

    Citation/source metadata is separate from the answer text.
    """

    if not query or not str(query).strip():
        return {
            "answer": "Please enter a question.",
            "insufficient_evidence": True,
            "citations": [],
        }

    clean_query_text = str(query).strip()

    try:
        hits = _retrieve(
            clean_query_text,
            tenant_id,
            top_k,
        )
    except Exception:
        logger.exception(
            "FixFlow RAG retrieval failed"
        )
        raise

    if not hits:
        return {
            "answer": INSUFFICIENT_EVIDENCE,
            "insufficient_evidence": True,
            "citations": [],
        }

    context = _build_context(hits)

    prompt = build_prompt(
        query=clean_query_text,
        context=context,
        domain=kwargs.get("domain"),
    )

    response = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        max_tokens=3000,
        extra_body={
            "reasoning_effort": "medium",
        },
    )

    answer = (
        response.choices[0].message.content or ""
    ).strip()

    if _is_insufficient(answer):
        return {
            "answer": INSUFFICIENT_EVIDENCE,
            "insufficient_evidence": True,
            "citations": [],
        }

    # Defensive cleanup: the prompt prohibits citations in answers.
    # Remove common trailing source/citation markers if the model
    # nevertheless adds them.
    answer = re.sub(
        r"\s*\[(?:\d+(?:\s*,\s*\d+)*)\]",
        "",
        answer,
    ).strip()

    return {
        "answer": answer,
        "insufficient_evidence": False,
        "citations": _citations_from_hits(hits),
    }
