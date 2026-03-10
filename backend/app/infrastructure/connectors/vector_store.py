"""ChromaDB vector store for connector file search."""

from __future__ import annotations

import logging
from pathlib import Path

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "connector_files"
_CHROMA_PATH = Path(settings.file_storage_path) / ".chroma"


def _get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(_CHROMA_PATH))


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def index_files(
    connector_id: str,
    provider: str,
    files: list[dict],
) -> None:
    """Index connector files into ChromaDB.

    Each file dict should have: name, path, file_type, text_content.
    """
    if not files:
        return

    client = _get_client()
    collection = _get_collection(client)

    ids = [f"{connector_id}:{f['name']}" for f in files]
    documents = [f["text_content"] for f in files]
    metadatas = [
        {
            "connector_id": connector_id,
            "provider": provider,
            "name": f["name"],
            "path": f["path"],
            "file_type": f["file_type"],
        }
        for f in files
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Indexed %d files for %s into ChromaDB", len(files), provider)


def remove_files(connector_id: str) -> None:
    """Remove all files for a connector from ChromaDB."""
    client = _get_client()
    collection = _get_collection(client)

    # Get all IDs for this connector and delete them
    results = collection.get(where={"connector_id": connector_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])
        logger.info("Removed %d files from ChromaDB for connector %s", len(results["ids"]), connector_id)


def search(
    query: str,
    connector_id: str | None = None,
    n_results: int = 10,
) -> list[dict]:
    """Search connector files by semantic similarity.

    Returns list of dicts with: name, path, file_type, text_content, provider, score.
    """
    client = _get_client()
    collection = _get_collection(client)

    if collection.count() == 0:
        return []

    where = {"connector_id": connector_id} if connector_id else None
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    files = []
    for i, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        files.append({
            "name": meta["name"],
            "path": meta["path"],
            "file_type": meta["file_type"],
            "text_content": results["documents"][0][i],
            "provider": meta["provider"],
            "score": 1 - distance,  # cosine similarity
        })

    return files
