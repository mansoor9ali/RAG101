# -*- coding: utf-8 -*-
"""
Vector store service module
"""
import os
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
from utils.decorators import error_handler, log_execution

from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import (
    EMBEDDING_MODEL, 
    EMBEDDING_BASE_URL, 
    MAX_RETRIEVED_DOCS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SEPARATORS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Vector store service class for managing document vector storage
    """
    # 1. Initialize vector store service
    def __init__(self, index_dir: str = "faiss_index"):
        """
        index_dir - Index directory
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        self.vector_store = None
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=EMBEDDING_BASE_URL)
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=SEPARATORS
        )
    
    # 2. Update embedding model
    def update_embedding_model(self, model_name: str) -> bool:
        """
        model_name - New embedding model name

        @return Whether update succeeded
        """
        try:
            if self.embeddings.model != model_name:
                self.embeddings = OllamaEmbeddings(model=model_name, base_url=EMBEDDING_BASE_URL)
                logger.info(f"Embedding model updated to: {model_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update embedding model: {str(e)}")
            return False
    
    # 3. Text splitting method
    @error_handler()
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks

        @param documents - Original document list
        @return Chunked document list
        """
        try:
            # Use text splitter for chunking
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"Document splitting complete: original count {len(documents)}, chunked count {len(split_docs)}")
            return split_docs
        except Exception as e:
            logger.error(f"Document splitting failed: {str(e)}")
            # If splitting fails, return original documents
            return documents

    # 4. Create a brand new vector store instance (overwrites existing data)
    @error_handler()
    def create_vector_store(self, documents: List[Document]) -> Optional[FAISS]:
        """
        documents - Document list

        @return FAISS vector store
        """
        if not documents:
            logger.warning("No documents available to create vector store")
            return None
        
        logger.info(f"Creating vector store, original document count: {len(documents)}")
        
        try:
            # Chunk documents
            split_documents = self.split_documents(documents)
            
            # Use LangChain's FAISS vector store
            self.vector_store = FAISS.from_documents(
                split_documents,
                self.embeddings
            )
            
            # Save vector store
            self._save_vector_store(self.vector_store)
            
            logger.info(f"Vector store created successfully with {len(split_documents)} chunks")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            return None
    
    # 5. Save vector store
    def _save_vector_store(self, vector_store: FAISS):
        """
        vector_store - FAISS vector store
        """
        try:
            vector_store.save_local(str(self.index_dir))
            logger.info(f"Vector store saved to: {self.index_dir}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {str(e)}")
    
    # 6. Load vector store
    @error_handler()
    def load_vector_store(self) -> Optional[FAISS]:
        """
        @return FAISS vector store
        """
        try:
            if (self.index_dir / "index.faiss").exists():
                self.vector_store = FAISS.load_local(
                    str(self.index_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Vector store loaded successfully")
                return self.vector_store
            logger.warning("Vector store files do not exist")
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
        return None
    

    # 7. Search related documents
    @error_handler()
    def search_documents(self, query: str, threshold: float = 0.7) -> List[Document]:
        """
        query - Query text
        threshold - Similarity threshold

        @return List of related documents
        """
        if not self.vector_store:
            self.vector_store = self.load_vector_store()
            if not self.vector_store:
                logger.warning("Vector store not initialized")
                return []
        
        try:
            # Use LangChain similarity search
            docs_and_scores = self.vector_store.similarity_search_with_score(
                query,
                k=MAX_RETRIEVED_DOCS
            )
            
            # Filter results by threshold
            results = [doc for doc, score in docs_and_scores if score > threshold]
            
            logger.info(f"Found {len(results)} related documents, similarity threshold: {threshold}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            return []
    
    # 8. Get document context
    def get_context(self, docs: List[Document]) -> str:
        """
        docs - Document list

        @return Merged context string
        """
        if not docs:
            return ""
        return "\n\n".join(doc.page_content for doc in docs)
    

    # 9. Add a single document to vector store (append without rebuilding entire store)
    @error_handler()
    def add_document(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a single document to the vector store

        @param {str} content - Document content
        @param {Dict[str, Any]} metadata - Document metadata
        @return {bool} Whether addition succeeded
        """
        if not content:
            logger.warning("Document content is empty; cannot add")
            return False
            
        try:
            # Create Document object
            doc = Document(page_content=content, metadata=metadata or {})
            
            # Chunk the document
            split_docs = self.split_documents([doc])
            
            # If vector store doesn't exist, try loading
            if not self.vector_store:
                self.vector_store = self.load_vector_store()
                if not self.vector_store:
                    # If still not present, create a new vector store with this document
                    self.vector_store = self.create_vector_store([doc])
                    return True
            
            # Add chunks to existing vector store
            self.vector_store.add_documents(split_docs)
            
            # Save updated vector store
            self._save_vector_store(self.vector_store)
            
            logger.info(f"Successfully added document, title: {metadata.get('source', 'unknown') if metadata else 'unknown'}, chunks: {len(split_docs)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            return False
    

    # 10. Clear index (delete all index files)
    def clear_index(self):
        try:
            for file in self.index_dir.glob("*"):
                file.unlink()
            self.vector_store = None
            logger.info("Index cleared")
        except Exception as e:
            logger.error(f"Failed to clear index: {str(e)}")
            raise 