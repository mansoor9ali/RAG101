import os


from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rich import print

from MultiQueryRetriever import MultiQueryRetriever
from dotenv import load_dotenv

from embeddingsUtiles import load_embedding_model
from utiles import get_retriever, load_pdf_docling

load_dotenv()


def get_query(input_dict):
    """Extract query from input dict or return string as-is."""
    if isinstance(input_dict, dict):
        return input_dict.get("question", input_dict.get("input", str(input_dict)))
    return str(input_dict)


if __name__ == '__main__':
    query = "What are the specific factors contributing to Airbnb's increased operational expenses in the last fiscal year?"
    llm = init_chat_model(
        model="deepseek-reasoner",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        model_provider="openai",
        temperature=0
    )

    # Decomposition
    template = """You are a helpful assistant that generates multiple sub-questions related to an input question.
    The goal is to break down the input into a set of sub-problems / sub-questions that can be answers in isolation.
    Generate multiple search queries related to: {question}
    Output (5 queries):"""

    decomposition_prompt = ChatPromptTemplate.from_template(template)

    # Chain
    generate_queries_decomposition = (decomposition_prompt | llm | StrOutputParser() | (lambda x: x.split("\n")))

    # Run
    questions = generate_queries_decomposition.invoke({"question": query})

    print('Generated Sub-Questions:')
    print(questions)



    print("-----------------------------------------")    # Load your retriever here (e.g., Chroma, FAISS, etc.)


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

    # ============================================
    # The Embedding Model
    # ============================================
    embedding_model = load_embedding_model()

    abnb_retriever = get_retriever(docs, embedding_model, top_k=10, collection_name="airbnb-1")

    prompt_template = """
    You are a helpful assistant. Provide answers to users questions based on the provided context.

    Context:
    {context}

    Question:
    {question}


    """
    prompt = ChatPromptTemplate.from_template(prompt_template)

    # Create multi-query retriever
    final_retriever = MultiQueryRetriever.from_llm(abnb_retriever, llm)

    # Create chain with proper query extraction
    chain = {
                "question": RunnablePassthrough(),
                "context": RunnableLambda(get_query) | final_retriever
            } | prompt | llm | StrOutputParser()

    result = chain.invoke(query)

    
    print(result)


