import logging
import os
import pathlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

from langchain.docstore.document import Document
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PDFMinerLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)

DOCUMENT_MAP = {
    ".txt": {
        "loader": TextLoader,
        "language": None,
    },
    ".html": {
        "loader": TextLoader,
        "language": Language.HTML,
    },
    ".md": {
        "loader": TextLoader,
        "language": Language.MARKDOWN,
    },
    ".py": {
        "loader": TextLoader,
        "language": Language.PYTHON,
    },
    ".pdf": {
        "loader": PDFMinerLoader,
        "language": None,
    },
    ".csv": {
        "loader": CSVLoader,
    },
    ".xls": {
        "loader": UnstructuredExcelLoader,
    },
    ".xlsx": {
        "loader": UnstructuredExcelLoader,
    },
    ".docx": {
        "loader": Docx2txtLoader,
        "language": None,
    },
    ".doc": {
        "loader": Docx2txtLoader,
        "language": None,
    },
    ".pptx": {
        "loader": UnstructuredPowerPointLoader,
    },
    ".ppt": {
        "loader": UnstructuredPowerPointLoader,
    },
}


def load_single_document(file_path: str) -> tuple[str, list[Document]]:
    """Load a single document from a file path."""
    logging.info(f"Loading {file_path}")
    file_extension = os.path.splitext(file_path)[1]
    ext_metadata = DOCUMENT_MAP.get(file_extension)
    if ext_metadata:
        loader_class = ext_metadata.get("loader")
        loader = loader_class(file_path)
    else:
        raise ValueError("Document type is undefined")
    return file_extension, loader.load()


def load_document_batch(filepaths: list[str]):
    """Load multiple documents in parallel."""
    logging.info("Loading document batch")
    # create a thread pool
    with ThreadPoolExecutor(len(filepaths)) as exe:
        # load files
        futures = [exe.submit(load_single_document, name) for name in filepaths]
        # collect data
        data_list = [future.result() for future in futures]
        # return data and file paths
        return (data_list, filepaths)


def load_documents(source_dir: pathlib.Path, ingest_threads: int) -> list[Document]:
    """Load all documents from the source documents directory."""
    all_files = source_dir.rglob("*")
    paths = []
    for file_path in all_files:
        file_extension = os.path.splitext(file_path)[1]
        source_file_path = os.path.join(source_dir, file_path)
        if file_extension in DOCUMENT_MAP.keys():
            paths.append(source_file_path)

    # Have at least one worker and at most INGEST_THREADS workers
    n_workers = min(ingest_threads, max(len(paths), 1))
    chunksize = round(len(paths) / n_workers)
    docs = []
    with ProcessPoolExecutor(n_workers) as executor:
        futures = []
        # split the load operations into chunks
        for i in range(0, len(paths), chunksize):
            # select a chunk of filenames
            filepaths = paths[i : (i + chunksize)]
            # submit the task
            future = executor.submit(load_document_batch, filepaths)
            futures.append(future)
        # process all results
        for future in as_completed(futures):
            # open the file and load the data
            contents, _ = future.result()
            docs.extend(contents)

    return docs


def split_document(document: Document, file_extension: str, chunk_size: int, chunk_overlap: int):
    """Split a document into chunks."""
    ext_metadata = DOCUMENT_MAP.get(file_extension)
    # If there is no language defined, don't chunk the text
    if "language" not in ext_metadata:
        chunks = [document]
    # If there is a language defined, chunk the text according to the language
    else:
        language = ext_metadata["language"]
        # If the language is None, use the basic splitter
        if language is None:
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        # Otherwise use the specific language
        else:
            splitter = RecursiveCharacterTextSplitter.from_language(language=language, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(documents=[document])
    return chunks
