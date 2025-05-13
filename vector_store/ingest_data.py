"""Data Ingestion"""

import logging
import pathlib
from datetime import datetime

import pandas as pd
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from constants import (
    DEVICE,
    DIRECTORY_PATH,
    KNOWLEDGE_REPOSITORY_PATH,
    PGVECTOR_DATABASE_NAME,
    PGVECTOR_HOST,
    PGVECTOR_PASS,
    PGVECTOR_PORT,
    PGVECTOR_USER,
)
from split import load_documents, split_document

logger = logging.getLogger(__name__)


def get_embedder(embedding_model_name: str) -> HuggingFaceEmbeddings:
    """Initialize an embedder to convert text into vectors."""
    return HuggingFaceEmbeddings(
        model_name=embedding_model_name,
        model_kwargs={"device": DEVICE},
        show_progress=True,
    )


def ingest(
    meta_lookup: dict[pathlib.Path, dict],
    collection_name: str,
    chunk_size: int,
    chunk_overlap: int,
    ingest_threads: int = 8,
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    mode: str = "overwrite",
    collection_metadata: dict = {},
):
    """Load documents into a vectorstore."""
    # Get documents
    all_documents = []
    origin_urls = {}
    documents = load_documents(KNOWLEDGE_REPOSITORY_PATH, ingest_threads=ingest_threads)
    for extension, document in documents:
        # Split each document into chunks
        document = document[0]
        # Rename "source" to "_source" and save filename to "source"
        source = pathlib.Path(document.metadata["source"])
        file_name = source.stem
        document.metadata["_source"] = document.metadata["source"]
        document.metadata["source"] = file_name
        chunks = split_document(
            document, extension, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        # Attach metadata to each chunk
        for chunk in chunks:
            path_metadata = meta_lookup.get(source, {})
            chunk.metadata = chunk.metadata | path_metadata
        # Record how many chunks were made
        rel_path = source.relative_to(KNOWLEDGE_REPOSITORY_PATH)
        origin = rel_path.parts[0]
        origin_url = (origin, chunk.metadata.get("url"))
        origin_urls[origin_url] = len(chunks)
        all_documents.extend(chunks)

    # Create embeddings
    embedder = get_embedder(embedding_model_name)

    # Build the Postgres connection string
    connection_string = PGVector.connection_string_from_db_params(
        driver="psycopg",
        host=PGVECTOR_HOST,
        port=int(PGVECTOR_PORT),
        database=PGVECTOR_DATABASE_NAME,
        user=PGVECTOR_USER,
        password=PGVECTOR_PASS,
    )

    # Connect to the db
    db = PGVector(
        connection=connection_string,
        embeddings=embedder,
        collection_name=collection_name,
        collection_metadata=collection_metadata,
        use_jsonb=True,
    )

    # Overwrite the collection (if requested)
    if mode == "overwrite":
        db.delete_collection()
        logger.info(f"Collection {collection_name} deleted")
        db.create_collection()
        logger.info(f"Collection {collection_name} created")

    # Load the documents
    logger.info(
        f"Loading {len(all_documents)} embeddings to {PGVECTOR_HOST} - {PGVECTOR_DATABASE_NAME} - {collection_name}"
    )

    # Add documents to DB in batches to accomodate the large numbers of parameters
    batch_size = 150
    for i in range(0, len(all_documents), batch_size):
        batch = all_documents[i:i + batch_size]
        logger.info(f"Ingesting batch {i // batch_size + 1} of {len(batch)} documents")
        db.add_documents(documents=batch)

    logger.info(f"Successfully loaded {len(all_documents)} embeddings")

    directory_source_url_chunks = [
        list(origin_url) + [chunks] for origin_url, chunks in origin_urls.items()
    ]
    df = pd.DataFrame(directory_source_url_chunks, columns=["origin", "url", "chunks"])
    filename = f"{PGVECTOR_HOST} - {collection_name} - {datetime.now()}.csv"
    outpath = DIRECTORY_PATH / "logs" / filename
    outpath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(outpath, index=False)
