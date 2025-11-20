import os
import time

from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from rich import print

from embeddingsUtiles import load_embedding_model
from utiles import load_pdf, get_retriever, retrieve_context, load_pdf_docling

load_dotenv()

if __name__ == '__main__':
    print('Starting Reranking RAG example...')
    if not os.path.exists("./data"):
        os.mkdir("./data")

    documents = load_pdf_docling("./data/8a9ebed0-815a-469a-87eb-1767d21d8cec.pdf")

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        # separators=["\n\n\n", "\n\n"],
        chunk_size=1024,
        chunk_overlap=0,
        model_name="gpt-4",
        add_start_index=True,  # If `True`, includes chunk's start index in metadata
        strip_whitespace=True,  # If `True`, strips whitespace from the start and end of every document
    )

    docs = text_splitter.split_documents(documents)

    print(f"Split into {len(docs)} chunks of text")

    #============================================
    # The Embedding Model
    # ============================================
    embedding_model = load_embedding_model()

    abnb_retriever = get_retriever(docs, embedding_model, top_k=10, collection_name="airbnb-1")

    query = "What are the specific factors contributing to Airbnb's increased operational expenses in the last fiscal year?"
    similar_chunks = retrieve_context(query, retriever=abnb_retriever, remove_duplicates=True )
    print(f"Retrieved {len(similar_chunks)} similar chunks:")
    for i, chunks in enumerate(similar_chunks):
        print(f"--------------------------------- chunk # {i} -------------------------------------")
        print(chunks.page_content[:800])

    print(f"---------------------------------------------------------------------------------")
    print('Now do Reranking ....')
    print(f"---------------------------------------------------------------------------------")
    llm_reranker = init_chat_model(
        model="deepseek-reasoner",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        model_provider="openai",
        temperature=0
    )
    start = time.time()

    # Create prompt for reranking
    rerank_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert relevance ranker. Given a list of documents and a query, your job is to determine how relevant each document is for answering the query.
    Your output must be valid JSON, which is a list of documents. Each document has two fields: content and score. score is from 0.0 to 100.0. Higher relevance means higher score."""),
        ("human", "Query: {query}\n\nDocs: {docs}")
    ])

    # Format documents for prompt
    docs_text = "\n\n".join([f"Document {i}: {doc.page_content}" for i, doc in enumerate(similar_chunks)])

    # Create chain and invoke
    chain = rerank_prompt | llm_reranker
    response = chain.invoke({"query": query, "docs": docs_text})

    print(f"Took {time.time() - start} seconds to re-rank documents with Deepseek Reasoner")
    print('################################################################')
    print('#################### EXAMPLE 1 ##############################')

    print('Answer:')
    print(response.content)
    print('################################################################')
    print('################################################################')

    print('############ NOW SORT WITH SCORE #############')
