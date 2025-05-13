import asyncio
import os
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PDFReader

from dotenv import load_dotenv

load_dotenv()

# Config
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
STORAGE_DIR = ROOT_DIR / "storage"

async def build_and_save_index():
    """Builds the index from PDF files and saves it."""
    print("Loading PDF documents...")
    reader = PDFReader()
    pdf_files = list(DATA_DIR.glob("**/*.pdf"))
    
    documents = []
    for pdf_file in pdf_files:
        documents.extend(reader.load_data(file=pdf_file))
    
    print(f"Loaded {len(documents)} document chunks from {len(pdf_files)} PDF files")

    print("Building index...")
    index = VectorStoreIndex.from_documents(documents)

    print(f"Saving index to {STORAGE_DIR}/...")
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    return index

async def load_or_build_index():
    """Loads existing index or builds a new one if not found."""
    if os.path.exists(STORAGE_DIR) or False:
        print(f"Loading existing index from {STORAGE_DIR}/...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
    else:
        index = await build_and_save_index()
    return index

async def main():
    # Step 1: Setup global Settings
    Settings.embed_model = OpenAIEmbedding(api_key=os.getenv("OPENAI_API_KEY"))
    Settings.llm = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )

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
