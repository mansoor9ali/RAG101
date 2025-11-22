import os
from typing import List, Optional
import fitz  # PyMuPDF
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from sentence_transformers import SentenceTransformer, CrossEncoder
from langchain_core.embeddings import Embeddings
import torch
import numpy as np
import uuid
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from rich import print

load_dotenv()

# --- Embedding Model Wrapper ---
class BGEEmbeddings(Embeddings):
    """Custom embedding class that wraps SentenceTransformer for BGE models."""

    def __init__(self, model_name: str, device: str = None, normalize: bool = True):
        self.model_name = model_name
        self.normalize = normalize

        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

        self.device = device
        print(f"Loading embedding model: {model_name} on {device}...")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Loaded embedding model: {model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True
        )
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [[float(x) for x in emb] for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(
            text,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True
        )
        return [float(x) for x in embedding.tolist()]

# --- Global Model Instance (Lazy Loading) ---
_embedding_model = None
_reranker_model = None

def get_reranker_model():
    global _reranker_model
    if _reranker_model is None:
        # Using a small, fast cross-encoder
        _reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker_model

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = BGEEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            normalize=True
        )
    return _embedding_model

def get_text_embedding(text: str) -> List[float]:
    model = get_embedding_model()
    return model.embed_query(text)

# --- PDF Loading ---
def load_pdf(file_path: str) -> List[Document]:
    """Loads documents from PDF files using PyMuPDF."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")

        # Simple cleanup
        text = ' '.join(text.split()) # Remove extra whitespace
        
        document = Document(
            page_content=text,
            metadata={"source": file_path}
        )
        return [document]
    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
        raise

# --- Chunking ---
def split_text(documents: List[Document], chunk_size=1000, chunk_overlap=200) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
        strip_whitespace=True,
    )
    return text_splitter.split_documents(documents)

# --- Vector Store & Retrieval ---
def create_vector_store(docs: List[Document], collection_name: str = None):
    embedding_model = get_embedding_model()
    if collection_name is None:
        collection_name = f"rag_collection_{uuid.uuid4().hex[:8]}"
    
    vector_store = Chroma.from_documents(
        docs,
        embedding_model,
        collection_name=collection_name
    )
    return vector_store, collection_name

def retrieve_documents(query: str, collection_name: str, top_k: int = 5):
    embedding_model = get_embedding_model()
    # Re-initialize Chroma client for the existing collection
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model
    )
    
    # Get results with scores
    results = vector_store.similarity_search_with_score(query, k=top_k)
    return results

# --- Docling Conversion ---
def convert_to_markdown(file_path: str) -> str:
    """Converts a PDF to Markdown using Docling."""
    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        return result.document.export_to_markdown()
    except Exception as e:
        print(f"Error converting PDF {file_path} with Docling: {e}")
        raise

# --- LLM Generation ---
def generate_answer(query: str, context_chunks: List[str]) -> str:
    """Generates an answer using IBM Granite via Watsonx."""
    try:

        project_id = os.getenv("RAG_PROJECT_ID")
        if not project_id:
            return "Error: RAG_PROJECT_ID not set in .env"

        llm = init_chat_model(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            model_provider="openai",
            temperature=0.2,
        )

        prompt_template = ChatPromptTemplate.from_template(
            (
                "You are a helpful AI assistant. Answer the question based ONLY on the provided context.\n"
                "If the answer is not in the context, say 'I cannot answer this based on the provided documents.'\n\n"
                "Context:\n{context}\n\n"
                "Question: {question}"
            )
        )

        chain = prompt_template | llm | StrOutputParser()
        
        context_text = "\\n\\n".join(context_chunks)
        response = chain.invoke({"question": query, "context": context_text})
        
        return response
    except Exception as e:
        print(f"Error generating answer: {e}")
        return f"Error generating answer: {str(e)}"

from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ... (existing code)

# --- Parent-Child Chunking ---
# Global store for parent documents (in-memory for demo)
_parent_store = InMemoryStore()

def create_parent_child_index(docs: List[Document], collection_name: str = None):
    embedding_model = get_embedding_model()
    if collection_name is None:
        collection_name = f"pc_rag_{uuid.uuid4().hex[:8]}"
    
    # Child splitter (small chunks for retrieval)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    
    # Parent splitter (larger chunks for context)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model
    )
    
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=_parent_store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    
    retriever.add_documents(docs)
    
    return collection_name

def retrieve_parent_child(query: str, collection_name: str, top_k: int = 3):
    embedding_model = get_embedding_model()
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model
    )
    
    # We need to reconstruct the retriever to access the docstore
    # In a real app, we'd persist the docstore. For this demo, we use the global in-memory one.
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
    
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=_parent_store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    
    # Retrieve parent documents
    parents = retriever.invoke(query)
    
    # For visualization, we also want to see the child chunks that triggered the retrieval
    # This is a bit hacky as ParentDocumentRetriever hides this, so we'll do a raw search too
    raw_children = vectorstore.similarity_search_with_score(query, k=top_k * 2)
    
    return parents[:top_k], raw_children[:top_k]

# --- Query Expansion ---
def expand_query(original_query: str) -> List[str]:
    """Generates multiple search queries based on a single input query."""
    try:
        project_id = os.getenv("RAG_PROJECT_ID")
        if not project_id:
            return [original_query]

        llm = init_chat_model(
            model="deepseek-reasoner",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            model_provider="openai",
            temperature=0.5, # Higher temperature for variety
        )

        prompt_template = ChatPromptTemplate.from_template(
            (
                "You are a helpful expert research assistant. "
                "Your users are asking questions about a document. "
                "Suggest up to 3 additional related search queries to help them find the answer. "
                "Provide only the queries, one per line. Do not number them."
                "\n\nOriginal Question: {question}"
            )
        )

        chain = prompt_template | llm | StrOutputParser()
        
        response = chain.invoke({"question": original_query})
        
        # Parse response into list
        expanded_queries = [q.strip() for q in response.split('\n') if q.strip()]
        
        # Ensure original query is included first
        if original_query not in expanded_queries:
            expanded_queries.insert(0, original_query)
            
        return expanded_queries[:5] # Limit to 5 total
    except Exception as e:
        print(f"Error expanding query: {e}")
        return [original_query]

# --- Reranking ---
def rerank_documents(query: str, documents: List[Document], top_k: int = 3):
    reranker = get_reranker_model()
    
    # Prepare pairs for cross-encoder
    pairs = [[query, doc.page_content] for doc in documents]
    
    # Predict scores
    scores = reranker.predict(pairs)
    
    # Combine docs with scores
    scored_docs = []
    for i, doc in enumerate(documents):
        score = float(scores[i])
        if np.isnan(score):
            score = 0.0
        scored_docs.append((doc, score))
    
    # Sort by score descending
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return scored_docs[:top_k]

