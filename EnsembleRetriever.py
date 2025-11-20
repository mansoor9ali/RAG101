
from langchain_community.retrievers.bm25 import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import Runnable
from typing import List, Any
from collections import defaultdict

# Custom EnsembleRetriever Implementation
# (EnsembleRetriever may not be available in some LangChain versions)
class EnsembleRetriever(Runnable):
    """
    Custom implementation of ensemble retriever.
    Combines results from multiple retrievers with weighted scores.
    """
    def __init__(self, retrievers: List[Any], weights: List[float] = None):
        """
        Initialize ensemble retriever.

        Args:
            retrievers: List of retriever objects to combine
            weights: List of weights for each retriever (defaults to equal weights)
        """
        super().__init__()
        self.retrievers = retrievers

        if weights is None:
            weights = [1.0 / len(retrievers)] * len(retrievers)

        if len(weights) != len(retrievers):
            raise ValueError(f"Number of weights ({len(weights)}) must match number of retrievers ({len(retrievers)})")

        self.weights = weights

    @property
    def InputType(self):
        """Input type for Runnable."""
        return str

    @property
    def OutputType(self):
        """Output type for Runnable."""
        from langchain_core.documents import Document
        return List[Any]

    def invoke(self, input: Any, config: Any = None, **kwargs: Any):
        """Retrieve documents using ensemble of retrievers.

        Accepts either a string query or a dict with 'question' or 'input' key.
        """
        # Extract query string from input
        if isinstance(input, dict):
            query = input.get("question", input.get("input", ""))
        else:
            query = str(input)

        # Get documents from each retriever
        all_doc_scores = defaultdict(float)
        all_docs = {}

        for retriever, weight in zip(self.retrievers, self.weights):
            # Retrieve documents
            docs = retriever.invoke(query)

            # Assign scores based on rank (higher rank = higher score)
            # Documents are typically returned in order of relevance
            num_docs = len(docs)
            for rank, doc in enumerate(docs):
                # Use content hash as unique identifier
                doc_hash = hash(doc.page_content)

                # Calculate score: (num_docs - rank) / num_docs * weight
                # This gives higher scores to documents ranked higher
                if num_docs > 0:
                    score = ((num_docs - rank) / num_docs) * weight
                else:
                    score = weight

                # Store document if not seen before
                if doc_hash not in all_docs:
                    all_docs[doc_hash] = doc

                # Accumulate scores
                all_doc_scores[doc_hash] += score

        # Sort documents by combined score
        sorted_docs = sorted(
            all_docs.items(),
            key=lambda x: all_doc_scores[x[0]],
            reverse=True
        )

        # Return documents in order of combined scores
        return [doc for _, doc in sorted_docs]

    def get_relevant_documents(self, query: str):
        """Compatibility method for older API."""
        return self.invoke(query)


def get_ensemble_retriever(docs, embedding_model, collection_name="test", top_k=3) -> Any:
    """
    Initializes a retriever object to fetch the top_k most relevant documents based on cosine similarity.

    Parameters:
    - docs: A list of documents to be indexed and retrieved.
    - embedding_model: The embedding model to use for generating document embeddings.
    - top_k: The number of top relevant documents to retrieve. Defaults to 3.

    Returns:
    - A retriever object configured to retrieve the top_k relevant documents.

    Raises:
    - ValueError: If any input parameter is invalid.
    """

    # Hybrid search
    # Example of parameter validation (optional)
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    try:
        vector_store = Chroma.from_documents(
            docs,
            embedding_model,
            collection_name=collection_name,
        )

        retriever = vector_store.as_retriever(search_kwargs={"k":top_k})
        # retriever.k = top_k

        # add keyword search
        keyword_retriever = BM25Retriever.from_documents(docs)
        keyword_retriever.k =  3

        ensemble_retriever = EnsembleRetriever(retrievers=[retriever,
                                                    keyword_retriever],
                                        weights=[0.5, 0.5])

        return ensemble_retriever
    except Exception as e:
        print(f"An error occurred while initializing the retriever: {e}")
        raise
