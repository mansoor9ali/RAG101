from langchain_community.vectorstores import Chroma
from langchain_core.runnables import Runnable
from langchain_core.documents import Document
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Custom InMemoryStore Implementation
# (InMemoryStore may not be available in some LangChain versions)
class InMemoryStore:
    """
    Simple in-memory document store for ParentDocumentRetriever.
    Stores documents keyed by their IDs.
    """
    def __init__(self):
        self.store: Dict[str, Document] = {}

    def mget(self, keys: List[str]) -> List[Optional[Document]]:
        """Get multiple documents by keys."""
        return [self.store.get(key) for key in keys]

    def mset(self, key_value_pairs: List[tuple]) -> None:
        """Set multiple key-value pairs."""
        for key, value in key_value_pairs:
            self.store[key] = value

    def mdelete(self, keys: List[str]) -> None:
        """Delete multiple keys."""
        for key in keys:
            self.store.pop(key, None)

    def yield_keys(self, prefix: Optional[str] = None) -> List[str]:
        """Yield keys, optionally filtered by prefix."""
        if prefix:
            return [key for key in self.store.keys() if key.startswith(prefix)]
        return list(self.store.keys())

# Custom ParentDocumentRetriever Implementation
# (ParentDocumentRetriever may not be available in some LangChain versions)
class ParentDocumentRetriever(Runnable):
    """
    Retriever that returns parent documents instead of child chunks.

    Concept:
    - Splits documents into small "child" chunks for indexing (precise retrieval)
    - Stores larger "parent" documents separately
    - When retrieving: finds small chunks → returns parent documents (full context)
    """
    def __init__(
        self,
        vectorstore,
        docstore: InMemoryStore,
        child_splitter,
        parent_splitter,
        k: int = 4,
        search_kwargs: Optional[Dict] = None
    ):
        super().__init__()
        self.vectorstore = vectorstore
        self.docstore = docstore
        self.child_splitter = child_splitter
        self.parent_splitter = parent_splitter
        self.k = k
        self.search_kwargs = search_kwargs or {}

    @property
    def InputType(self):
        """Input type for Runnable."""
        return str

    @property
    def OutputType(self):
        """Output type for Runnable."""
        return List[Document]

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the retriever.

        Process:
        1. Split into parent documents
        2. For each parent, split into child chunks
        3. Store parents in docstore
        4. Index child chunks in vectorstore (with reference to parent)
        """
        parent_docs = self.parent_splitter.split_documents(documents)

        for parent_doc in parent_docs:
            # Create unique ID for parent
            parent_id = f"parent_{hash(parent_doc.page_content)}"

            # Store parent in docstore
            self.docstore.mset([(parent_id, parent_doc)])

            # Split parent into child chunks
            child_docs = self.child_splitter.split_documents([parent_doc])

            # Add parent_id to child metadata
            for child_doc in child_docs:
                if child_doc.metadata is None:
                    child_doc.metadata = {}
                child_doc.metadata["parent_id"] = parent_id

            # Add child chunks to vectorstore
            if child_docs:
                self.vectorstore.add_documents(child_docs)

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> List[Document]:
        """Retrieve parent documents for a query.

        Process:
        1. Query vectorstore with child chunks
        2. Extract parent_id from child chunks
        3. Retrieve parent documents from docstore
        4. Return unique parent documents
        """
        # Extract query string
        if isinstance(input, dict):
            query = input.get("question", input.get("input", ""))
        else:
            query = str(input)

        # Search in vectorstore (gets child chunks)
        search_kwargs = {**self.search_kwargs, "k": self.k}
        child_docs = self.vectorstore.similarity_search(query, **search_kwargs)

        # Get unique parent IDs
        parent_ids = set()
        for child_doc in child_docs:
            parent_id = child_doc.metadata.get("parent_id")
            if parent_id:
                parent_ids.add(parent_id)

        # Retrieve parent documents
        parent_docs = self.docstore.mget(list(parent_ids))

        # Filter out None values and return
        return [doc for doc in parent_docs if doc is not None]

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Compatibility method for older API."""
        return self.invoke(query)


def create_parent_retriever(
    docs,
    embeddings_model,
    collection_name="split_documents",
    top_k=5,
    persist_directory=None,
):

    """
    Initializes a retriever object to fetch the top_k most relevant documents based on cosine similarity.

    Parameters:
    - docs: A list of documents to be indexed and retrieved.
    - embedding_model: The embedding model to use for generating document embeddings.
    - collection_name: The name of the collection
    - top_k: The number of top relevant documents to retrieve. Defaults to 3.
    - persist_directory: directory where you want to store your vectorDB

    Returns:
    - A retriever object configured to retrieve the top_k relevant documents.

    Raises:
    - ValueError: If any input parameter is invalid.
    """

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    parent_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        separators=["\n\n\n", "\n\n", "\n", ".", ""],
        chunk_size=512,
        chunk_overlap=0,
        model_name="gpt-4",
        is_separator_regex=False,
    )

    # This text splitter is used to create the child documents
    child_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        separators=["\n\n\n", "\n\n", "\n", ".", ""],
        chunk_size=256,
        chunk_overlap=0,
        model_name="gpt-4",
        is_separator_regex=False,
    )

    # The vectorstore to use to index the child chunks
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings_model,
        persist_directory=persist_directory,
    )

    # The storage layer for the parent documents
    store = InMemoryStore()
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
        k=10,
    )
    retriever.add_documents(docs)


    return retriever, vectorstore.as_retriever()