import argparse
import logging
import pathlib
import yaml

from ingest_data import ingest
from knowledge_source import fetchall as fetch_source
from delete_knowledge import delete_knowledge

logger = logging.getLogger(__name__)

def parse_config(path: pathlib.Path):
    """Parse the configuration file."""
    if path.is_dir():
        raise ValueError(f"Config file {path} is a directory")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config

def main(args: argparse.Namespace):
    config_path = args.config
    config: dict = parse_config(config_path)
    ingest_threads = config.get("ingest_threads", 8)
    collections = config.get("collections", [])
    logs_folder_id = config.get("logs_folder_id", None)
    errors = []
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
            embedding_model_name = collection.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            metadata = collection.get("metadata", {})
            sources = collection.get("sources", [])
            meta_lookup = {}
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
                logs_folder_id=logs_folder_id,
            )
        except Exception as e:
            raise e
        finally:
            delete_knowledge()

    if len(errors):
        raise Exception(errors)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=pathlib.Path, help="Path to config file.", default=pathlib.Path("config.yaml"))
    args = parser.parse_args()
    main(args)
