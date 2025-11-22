# -*- coding: utf-8 -*-
# @File    : app.py
# @Description: Main application file

import streamlit as st
import logging
import re
from Agentic_RAG.config.settings import (
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    DEFAULT_SIMILARITY_THRESHOLD,
    EMBEDDING_MODEL,
    AVAILABLE_EMBEDDING_MODELS
)
# RAGAgent: Agent to handle user input and generate responses, encapsulating model interaction logic.
from Agentic_RAG.models.agent import RAGAgent
# ChatHistoryManager: Manage chat history
from Agentic_RAG.utils.chat_history import ChatHistoryManager
# DocumentProcessor: Process user-uploaded documents
from Agentic_RAG.utils.document_processor import DocumentProcessor
# VectorStoreService: Vector database service for document indexing and retrieval
from Agentic_RAG.services.vector_store import VectorStoreService
# UIComponents: UI components for rendering the interface
from Agentic_RAG.utils.ui_components import UIComponents
from Agentic_RAG.utils.decorators import error_handler, log_execution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class App:
    """
    Main RAG application class
    """
    def __init__(self):
        """
        @description Initialize the application
        """
        self._init_session_state()  # Initialize session state
        self.chat_history = ChatHistoryManager()  # Create chat history manager
        self.document_processor = DocumentProcessor()  # Create document processor
        self.vector_store = VectorStoreService()  # Create vector store service
        logger.info("Application initialized successfully")
    
    # 1. Initialize session state
    @error_handler(show_error=False)
    def _init_session_state(self):
        if 'model_version' not in st.session_state:
            st.session_state.model_version = DEFAULT_MODEL  # Set default model
        if 'processed_documents' not in st.session_state:
            st.session_state.processed_documents = []  # Initialize processed document list
        if 'similarity_threshold' not in st.session_state:
            st.session_state.similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD  # Set default similarity threshold
        if 'rag_enabled' not in st.session_state:
            st.session_state.rag_enabled = True  # Enable RAG by default
        if 'embedding_model' not in st.session_state:
            st.session_state.embedding_model = EMBEDDING_MODEL  # Set default embedding model
    
    # 2. Render sidebar
    @error_handler()
    @log_execution
    def render_sidebar(self):
        # Update model selection and embedding model selection
        st.session_state.model_version, new_embedding_model = UIComponents.render_model_selection(
            AVAILABLE_MODELS,
            st.session_state.model_version,
            AVAILABLE_EMBEDDING_MODELS,
            st.session_state.embedding_model
        )
        
        # Check if embedding model has changed
        previous_embedding_model = st.session_state.embedding_model
        st.session_state.embedding_model = new_embedding_model
        
        # Update RAG settings
        st.session_state.rag_enabled, st.session_state.similarity_threshold = UIComponents.render_rag_settings(
            st.session_state.rag_enabled,
            st.session_state.similarity_threshold,
            DEFAULT_SIMILARITY_THRESHOLD
        )
        
        # Update the embedding model used by the vector store service
        if previous_embedding_model != st.session_state.embedding_model:
            if self.vector_store.update_embedding_model(st.session_state.embedding_model):
                # If a vector store already exists, remind the user to reprocess documents for the new embedding model
                if len(st.session_state.processed_documents) > 0:
                    st.sidebar.info(f"⚠️ Embedding model has changed to {st.session_state.embedding_model}. You may need to reprocess documents to use the new embedding model.")
        
        # Render chat statistics
        UIComponents.render_chat_stats(self.chat_history)
    

    # 3. Render document upload area
    @error_handler()
    @log_execution
    def render_document_upload(self):
        all_docs, self.vector_store = UIComponents.render_document_upload(
            self.document_processor,
            self.vector_store,
            st.session_state.processed_documents
        )
    
    # 4. Process user input
    @error_handler()
    @log_execution
    def process_user_input(self, prompt: str):
        """
        prompt - User input text

        1) RAG mode: retrieve related documents → build context → call the model
        2) Simple mode: call the model directly
        """
        self.chat_history.add_message("user", prompt)  # Add user message to chat history
        if st.session_state.rag_enabled:
            self._process_rag_query(prompt)  # If RAG is enabled, process RAG query
        else:
            self._process_simple_query(prompt)  # Otherwise, process simple query
    
    
    # 5. Process RAG query
    @error_handler()
    @log_execution
    def _process_rag_query(self, prompt: str):
        """
        prompt - User input text
        """
        with st.spinner("🤔 Evaluating your query..."): 
            # Search for relevant documents
            docs = self.vector_store.search_documents(  
                prompt,
                st.session_state.similarity_threshold
            )
            logger.info(f"Number of retrieved documents: {len(docs)}")  
            # Build document context
            context = self.vector_store.get_context(docs)  
            # Create RAG agent
            agent = RAGAgent(st.session_state.model_version)  
            # Run agent to get response
            response = agent.run(  
                prompt, 
                context=context
            )
            # Process response
            self._process_response(response, docs)  
    

    # 6. Process simple query
    @error_handler()
    @log_execution
    def _process_simple_query(self, prompt: str):
        """
        prompt - User input text
        """
        with st.spinner("🤖 Thinking..."): 
            # Create RAG agent
            agent = RAGAgent(st.session_state.model_version)  
            # Run agent to get response
            response = agent.run(prompt)  
            # Process response
            self._process_response(response)  
    
    
    # 7. Process agent response
    def _process_response(self, response: str, docs=None):
        """
        response - Raw response from the model
        docs - Retrieved documents (optional)
        """
        # 7.1 Handle the reasoning segment in the response
        think_pattern = r'<think>([\s\S]*?)</think>'  # Define regex pattern for reasoning content
        think_match = re.search(think_pattern, response)  # Search for reasoning content
        if think_match:
            think_content = think_match.group(1).strip()  # Extract reasoning content
            response_wo_think = re.sub(think_pattern, '', response).strip()  # Remove reasoning section
        else:
            think_content = None
            response_wo_think = response
        
        # 7.2 Save the response to history
        self.chat_history.add_message("assistant", response_wo_think)  # Add assistant reply
        if think_content:
            self.chat_history.add_message("assistant_think", think_content)  # Add reasoning content
        if docs:
            doc_contents = [doc.page_content for doc in docs]  # Extract document content
            # Store retrieved documents as a single string entry in history
            combined_docs = "\n---\n".join(doc_contents)
            self.chat_history.add_message("retrieved_doc", combined_docs)  # Add retrieved documents


    # Entry point: run the application
    @error_handler()
    @log_execution
    def run(self):
        st.title("🐋 Qwen 3 Local RAG Reasoning Agent")  # Set application title
        st.info("**Qwen3:** The latest generation of the Qwen series LLMs, offering a comprehensive suite of dense and Mixture-of-Experts (MoE) models.")  # Show model info
        
        self.render_sidebar()  # Render sidebar
        self.render_document_upload()  # Render document upload area
        
        chat_col = st.columns([1])[0]  # Create chat column
        with chat_col:
            prompt = st.chat_input(  # Create chat input
                "Ask about your documents..." if st.session_state.rag_enabled else "Ask me anything..."
            )
            
            if prompt:
                self.process_user_input(prompt)  # Process user input
                
            # Render chat history
            UIComponents.render_chat_history(self.chat_history)
        
        mode_description = ""
        if st.session_state.rag_enabled:
            mode_description += "📚 RAG Mode: You can ask about the content of your uploaded documents."  
        else:
            mode_description += "💬 Chat Mode: Talk to the model directly."  
        
        mode_description += " 🌤️ Weather: You can ask about the weather in any city."  
            
        st.info(mode_description)  # Show mode description

if __name__ == "__main__":
            app = App()  # Create app instance
            app.run()  # Run the app