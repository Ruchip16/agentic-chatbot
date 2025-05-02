import asyncio
import os
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader

# Config
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
STORAGE_DIR = ROOT_DIR / "storage"

async def build_and_save_index():
    """Builds the index from PDF files and saves it."""
    print("Loading PDF documents...")
    reader = PDFReader()
    documents = reader.load_data(folder_path=DATA_DIR)

    print("Building index...")
    index = VectorStoreIndex.from_documents(documents)

    print(f"Saving index to {STORAGE_DIR}/...")
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    return index

async def load_or_build_index():
    """Loads existing index or builds a new one if not found."""
    if os.path.exists(STORAGE_DIR):
        print(f"Loading existing index from {STORAGE_DIR}/...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
    else:
        index = await build_and_save_index()
    return index

async def main():
    # Step 1: Setup global Settings
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
    Settings.llm = Ollama(model="llama3.1", request_timeout=360.0)

    # Step 2: Load or build the index
    index = await load_or_build_index()

    # Step 3: Create a query engine
    query_engine = index.as_query_engine()

    print("\n🔵 Chatbot ready! Type your questions (type 'exit' to quit):\n")

    while True:
        user_query = input("You: ")
        if user_query.lower() in ("exit", "quit"):
            print("Bye!")
            break
        response = await query_engine.aquery(user_query)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    asyncio.run(main())
