import os
import pathlib

import torch
from dotenv import load_dotenv

load_dotenv()

# PATHS
DIRECTORY_PATH = pathlib.Path(os.path.dirname(__file__)).parent
KNOWLEDGE_REPOSITORY_PATH = DIRECTORY_PATH / "knowledge"
SOURCE_RESPOSITORY_PATH = KNOWLEDGE_REPOSITORY_PATH / "source"

# INGEST
DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

# PGVECTOR
PGVECTOR_USER = os.environ.get("PGVECTOR_USER", None)
PGVECTOR_PASS = os.environ.get("PGVECTOR_PASS", None)
PGVECTOR_DATABASE_NAME = os.environ.get("PGVECTOR_DATABASE_NAME", None)
PGVECTOR_HOST = os.environ.get("PGVECTOR_URI", "localhost")
PGVECTOR_PORT = int(os.environ.get("PGVECTOR_PORT", 5432))
