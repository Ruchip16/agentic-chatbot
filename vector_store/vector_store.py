"""The Vector store service."""

import argparse
import logging
import pathlib
from typing import Any, List
import yaml

from ingest_data import ingest
from knowledge_source import fetchall as fetch_source
from delete_knowledge import delete_knowledge

logger = logging.getLogger(__name__)


def parse_config(path: pathlib.Path) -> dict[str, Any]:
    """Parse the YAML configuration file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist")
    if path.is_dir():
        raise ValueError(f"Expected a file but got a directory: {path}")

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Invalid configuration format in {path}")

    return config


def main(args: argparse.Namespace) -> None:
    """
    Ingests multiple document collections into a vector store
    using the configuration file specified in `args.config`.

    Args:
        args: Parsed arguments containing the config file path.
    """
    config_path = args.config
    config: dict = parse_config(config_path)
    ingest_threads = config.get("ingest_threads", 8)
    collections = config.get("collections", [])
    errors: List[Exception] = []
    for collection in collections:
        try:
            name = collection.get("id")
            mode = collection.get("mode")
            chunk_size = collection.get("chunk_size")
            chunk_overlap = collection.get("chunk_overlap")
            required_values = [name, mode, chunk_size, chunk_overlap]
            if any(value is None for value in required_values):
                required_keys = ["name", "mode", "chunk_size", "chunk_overlap"]
                raise ValueError(f"Missing required keys in collection {required_keys}")
            embedding_model_name = collection.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            )
            metadata = collection.get("metadata", {})
            sources = collection.get("sources", [])
            meta_lookup: dict[pathlib.Path, dict[Any, Any]] = {}
            for source in sources:
                source_meta_lookup = fetch_source(**source)
            meta_lookup = meta_lookup | source_meta_lookup
            ingest(
                meta_lookup=meta_lookup,
                collection_name=name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                ingest_threads=ingest_threads,
                embedding_model_name=embedding_model_name,
                mode=mode,
                collection_metadata=metadata,
            )
        except Exception as e:
            logger.error(
                "Failed to ingest collection %s: %s", collection.get("id", "unknown"), e
            )
            errors.append(e)
        finally:
            delete_knowledge()

    if errors:
        error_messages = "\n".join(str(e) for e in errors)
        raise RuntimeError(
            f"Ingest failed for {len(errors)} collection(s):\n{error_messages}"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        help="Path to config file.",
        default=pathlib.Path("./config/config.yaml"),
    )
    main(parser.parse_args())
