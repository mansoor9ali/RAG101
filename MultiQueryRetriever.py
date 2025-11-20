from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Any

# Custom Multi-Query Retriever Implementation
# (MultiQueryRetriever may not be available in some LangChain versions)
class MultiQueryRetriever(Runnable):
    """
    Custom implementation of multi-query retriever.
    Generates multiple query variations and retrieves documents for each.
    """
    def __init__(self, retriever, llm, num_queries=3):
        super().__init__()
        self.retriever = retriever
        self.llm = llm
        self.num_queries = num_queries

        # Prompt for generating query variations
        self.query_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI language model assistant. Your task is to generate {num_queries} different versions of the given user question to retrieve relevant documents from a vector database. By generating multiple perspectives on the user question, your goal is to help the user overcome some of the limitations of distance-based semantic search. Provide these alternative questions separated by newlines."),
            ("human", "Original question: {question}")
        ])

    @property
    def InputType(self):
        """Input type for Runnable."""
        return str

    @property
    def OutputType(self):
        """Output type for Runnable."""
        from langchain_core.documents import Document
        return List[Any]

    @classmethod
    def from_llm(cls, retriever, llm, num_queries=3):
        """Create MultiQueryRetriever from a base retriever and LLM."""
        return cls(retriever, llm, num_queries)

    def _generate_queries(self, question: str) -> List[str]:
        """Generate multiple query variations."""
        chain = self.query_generation_prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "question": question,
            "num_queries": self.num_queries
        })

        # Parse the generated queries (split by newlines)
        queries = [q.strip() for q in result.split("\n") if q.strip()]

        # Always include the original question
        if question not in queries:
            queries.insert(0, question)

        # Limit to num_queries
        return queries[:self.num_queries]

    def invoke(self, input: Any, config: Any = None, **kwargs: Any):
        """Retrieve documents using multiple query variations.

        Accepts either a string query or a dict with 'question' or 'input' key.
        """
        # Extract query string from input
        if isinstance(input, dict):
            query = input.get("question", input.get("input", ""))
        else:
            query = str(input)

        # Generate query variations
        queries = self._generate_queries(query)

        # Retrieve documents for each query
        all_docs = []
        seen_docs = set()

        for q in queries:
            docs = self.retriever.invoke(q)
            for doc in docs:
                # Use content hash to deduplicate
                doc_hash = hash(doc.page_content)
                if doc_hash not in seen_docs:
                    seen_docs.add(doc_hash)
                    all_docs.append(doc)

        return all_docs

    def get_relevant_documents(self, query: str):
        """Compatibility method for older API."""
        return self.invoke(query)

