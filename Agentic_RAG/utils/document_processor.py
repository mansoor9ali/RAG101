"""
Document processing module
"""
import os
import hashlib
import json
from typing import List, Optional, Dict, Any, Union
import logging
from pathlib import Path
import io
import tempfile

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from Agentic_RAG.utils.decorators import error_handler, log_execution
from datetime import datetime
from Agentic_RAG.config.settings import CHUNK_SIZE, CHUNK_OVERLAP, SEPARATORS

from langchain_community.document_loaders import PyPDFLoader


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Document processor class for handling PDF documents
    """

    # 1. Initialize document processor
    def __init__(self, cache_dir: str = ".cache", max_workers: int = 4):
        """
        cache_dir - Cache directory
        max_workers - Maximum worker threads
        """
        self.cache_dir = Path(cache_dir)
        print(f"Cache directory set to: {self.cache_dir}")
        self.cache_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=SEPARATORS,
            length_function=len,
            is_separator_regex=False
        )
    
    # 2. Get cache file path
    def _get_cache_path(self, file_content: bytes, file_name: str) -> Path:
        """
        file_content - File content
        file_name - File name

        @return Cache file path
        """
        cache_key = hashlib.md5(file_content + file_name.encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.json"
    
    # 3. Load processed result from cache
    def _load_from_cache(self, cache_path: str) -> Optional[List[Document]]:
        """
        @param {str} cache_path - Cache file path
        @return {Optional[List[Document]]} Processed result; None if cache doesn't exist
        """
        try:
            path = Path(cache_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Document(**doc) for doc in data]
        except Exception as e:
            logger.warning(f"Failed to load from cache: {str(e)}")
        return None
    
    # 4. Save processed result to cache
    def _save_to_cache(self, cache_path: Path, documents: List[Document]):
        """
        @param {Path} cache_path - Cache file path
        @param {List[Document]} documents - Processed documents
        """
        try:
            # Convert Document objects to serializable dicts
            docs_data = [doc.dict() for doc in documents]
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(docs_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save to cache: {str(e)}")
    

    # 5. Process PDF file
    @error_handler()
    @log_execution
    def _process_pdf(self, file_content: bytes, file_name: str) -> List[Document]:
        """
        file_content - PDF file content
        file_name - PDF file name

        @return List of processed documents
        """
        # Check cache
        cache_path = self._get_cache_path(file_content, file_name)
        print(f"Cache path: {cache_path}")
        cached_docs = self._load_from_cache(str(cache_path))
        if cached_docs is not None:
            logger.info(f"Loaded from cache: {file_name}")
            return cached_docs
        
        # Process PDF
        logger.info(f"Processing file: {file_name}")
        
        try:
            # On Windows, NamedTemporaryFile opened with delete=True can't be reopened (permission error).
            # Use mkstemp to create a closed path we can reopen safely.
            temp_path = None
            try:
                fd, temp_path = tempfile.mkstemp(suffix='.pdf')
                os.close(fd)  # Close the low-level file descriptor immediately
                logger.debug(f"Created temporary file: {temp_path}")

                # Write the PDF content
                with open(temp_path, 'wb') as f:
                    f.write(file_content)

                # Load PDF via temporary path
                loader = PyPDFLoader(temp_path)
                documents = loader.load()
                logger.debug(f"Loaded documents: {len(documents)}")

                # Split documents using the text splitter
                split_docs = self.text_splitter.split_documents(documents)

                # Save to cache
                if split_docs:
                    self._save_to_cache(cache_path, split_docs)

                return split_docs
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        logger.debug(f"Deleted temporary file: {temp_path}")
                    except OSError as cleanup_err:
                        logger.warning(f"Failed to delete temp file {temp_path}: {cleanup_err}")
                
        except Exception as e:
            logger.error(f"Failed to process PDF file: {str(e)}")
            raise
    

    # 6. Clear all cache
    def clear_cache(self):
        try:
            for file in self.cache_dir.glob("*.json"):
                file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            raise


    # 7. Process uploaded file; supports multiple file types
    @error_handler()
    @log_execution
    def process_file(self, uploaded_file_or_content, file_name: str = None) -> Union[str, List[Document]]:
        """
        uploaded_file_or_content - Streamlit uploaded file object or raw file content
        file_name - File name (required when first parameter is raw content)

        @return  Processed result: either plain text content or list of Document objects
        """
        try:
            # Determine input type
            if hasattr(uploaded_file_or_content, 'getvalue') and hasattr(uploaded_file_or_content, 'name'):
                # Streamlit uploaded file object
                file_content = uploaded_file_or_content.getvalue()
                file_name = uploaded_file_or_content.name
            elif isinstance(uploaded_file_or_content, bytes) and file_name:
                # Directly passed file content and name
                file_content = uploaded_file_or_content
            else:
                raise ValueError("Invalid parameters: need a valid file object or file content with file name")
            
            # Handle according to file type
            if file_name.lower().endswith('.pdf'):
                docs = self._process_pdf(file_content, file_name)
                # If file was uploaded via Streamlit, return text content; otherwise return Document objects
                if hasattr(uploaded_file_or_content, 'getvalue'):
                    return "\n\n".join(doc.page_content for doc in docs)
                return docs
            elif file_name.lower().endswith('.txt'):
                return file_content.decode('utf-8')
            else:
                return f"Unsupported file type: {file_name}"
            
        except Exception as e:
            logger.error(f"Failed to process file: {str(e)}")
            raise Exception(f"Failed to process file: {str(e)}")
            