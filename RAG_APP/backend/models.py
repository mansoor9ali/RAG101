from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ProcessRequest(BaseModel):
    file_path: str
    chunk_size: int = 1000
    chunk_overlap: int = 200

class ProcessResponse(BaseModel):
    collection_name: str
    num_chunks: int
    preview_chunks: List[str]
    embedding_preview: Optional[List[float]] = None

class QueryRequest(BaseModel):
    query: str
    collection_name: str
    top_k: int = 5

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class QueryResponse(BaseModel):
    results: List[SearchResult]
    query_embedding: Optional[List[float]] = None

class RerankRequest(BaseModel):
    query: str
    initial_results: List[SearchResult]
    top_k: int = 3

class RerankResponse(BaseModel):
    results: List[SearchResult]
    query_embedding: Optional[List[float]] = None

class ConversionResponse(BaseModel):
    markdown_content: str

class GenerateRequest(BaseModel):
    query: str
    context_chunks: List[str]

class GenerateResponse(BaseModel):
    answer: str

class ExpansionRequest(BaseModel):
    query: str

class ExpansionResponse(BaseModel):
    queries: List[str]

class ParentChildResponse(BaseModel):
    parents: List[SearchResult]
    children: List[SearchResult]
    query_embedding: Optional[List[float]] = None
