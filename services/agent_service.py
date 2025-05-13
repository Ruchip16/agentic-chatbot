import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

# API Models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# Global variables
query_engine = None

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
    if os.path.exists(STORAGE_DIR):
        print(f"Loading existing index from {STORAGE_DIR}/...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
    else:
        index = await build_and_save_index()
    return index

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the FastAPI app."""
    global query_engine
    
    # Startup: Setup global Settings and initialize query engine
    Settings.embed_model = OpenAIEmbedding(api_key=os.getenv("OPENAI_API_KEY"))
    Settings.llm = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )
    
    # Load or build the index
    index = await load_or_build_index()
    
    # Create a query engine
    query_engine = index.as_query_engine()
    
    print("🔵 Chatbot API is ready to accept queries!")
    
    yield  # Application runs here
    
    # Shutdown: Optional cleanup (e.g., clear query_engine)
    print("🛑 Shutting down Chatbot API...")
    query_engine = None

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Agentic Chatbot API",
    description="API for querying a document-aware chatbot powered by LlamaIndex",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """Send a query to the chatbot and get a response"""
    if query_engine is None:
        raise HTTPException(status_code=503, detail="Query engine not initialized")
    
    try:
        response = await query_engine.aquery(request.query)
        return QueryResponse(response=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)