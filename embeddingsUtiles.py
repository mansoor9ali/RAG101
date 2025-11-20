from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
import torch
import numpy as np
from typing import List, Union
import os

# Note: IBM watsonx Platform does not currently offer embedding models via their API.
# We'll use HuggingFace BGE embeddings directly via sentence-transformers, which provides
# excellent quality and are free to use. These models run locally and don't require API calls.

class BGEEmbeddings(Embeddings):
    """Custom embedding class that wraps SentenceTransformer for BGE models."""

    def __init__(self, model_name: str, device: str = None, normalize: bool = True):
        """
        Initialize BGE embeddings.

        Args:
            model_name: HuggingFace model name (e.g., "BAAI/bge-small-en-v1.5")
            device: Device to use ("cpu", "cuda", "mps"). If None, auto-detects.
            normalize: Whether to normalize embeddings (recommended for cosine similarity)
        """
        self.model_name = model_name
        self.normalize = normalize

        # Auto-detect device if not specified
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

        self.device = device
        print(f"Loading embedding model: {model_name} on {device}...")

        # Load SentenceTransformer model directly (bypasses LangChain compatibility issues)
        self.model = SentenceTransformer(model_name, device=device)

        print(f"✅ Loaded embedding model: {model_name}")
        print(f"📍 Device: {device}")

        # Test to get dimension
        test_emb = self.embed_query("test")
        print(f"📊 Embedding dimension: {len(test_emb)}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True
        )
        # Convert NumPy array to native Python list
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [[float(x) for x in emb] for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        embedding = self.model.encode(
            text,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True
        )
        # Ensure native Python types (fixes ChromaDB NumPy compatibility)
        return [float(x) for x in embedding.tolist()]
def load_embedding_model(
    model_name = "BAAI/bge-large-en-v1.5",
    device = None
):
    """
    Loads a HuggingFace BGE Embedding model for text embeddings.

    Note: IBM watsonx Platform does not currently provide embedding models via API.
    Using HuggingFace BGE models which are state-of-the-art and free.

    Parameters:
    - model_name: The HuggingFace model name. Options:
        - "BAAI/bge-small-en-v1.5" (default): Fast, 384 dimensions, 33M params - good for most use cases
        - "BAAI/bge-base-en-v1.5": Balanced, 768 dimensions, 110M params
        - "BAAI/bge-large-en-v1.5": Best quality, 1024 dimensions, 335M params - slower but more accurate
    - device: Device to run on ("cpu", "cuda", "mps"). If None, auto-detects.

    Returns:
    - An instance of BGEEmbeddings configured with the specified model.

    Raises:
    - Exception: For any issues encountered during model loading.
    """
    try:
        embedding_model = BGEEmbeddings(
            model_name=model_name,
            device=device,
            normalize=True  # Important for cosine similarity
        )
        return embedding_model
    except Exception as e:
        print(f"❌ Error loading embedding model: {e}")
        print("💡 Tip: Make sure you have sentence-transformers installed: pip install sentence-transformers")
        raise
