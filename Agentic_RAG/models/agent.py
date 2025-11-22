"""
Agent model class
"""
from typing import Optional
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.reasoning import ReasoningTools
from agno.tools.function import Function
from Agentic_RAG.config.settings import DEFAULT_MODEL, AMAP_API_KEY

import logging

from Agentic_RAG.services.weather_tools import WeatherTools

logger = logging.getLogger(__name__)

class RAGAgent:
    """
    RAG agent class encapsulating interaction with the model
    """
    def __init__(self, model_version: str = DEFAULT_MODEL):
        """
        Initialize the RAG agent

        Args:
            model_version (str): Model version identifier
        """
        self.model_version = model_version
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """
        Create an Agent instance

        Returns:
            Agent: Configured Agent instance
        """
        # 1. Create weather query tool
        weather_tools = WeatherTools(AMAP_API_KEY)
        
        # 2. Create function object
        query_weather_function = Function(
            name="query_weather",
            description="Query the weather forecast for a specified city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city to query"
                    }
                },
                "required": ["city"]
            },
            entrypoint=weather_tools.query_weather
        )
        
        return Agent(
            name="Qwen 3 RAG Agent",
            model=Ollama(id=self.model_version),
            instructions="""You are an intelligent assistant capable of answering a wide range of user questions.
                            [Important Rules]
                            - In RAG mode, you must answer strictly based on the provided document content
                            - In normal chat mode, you may answer based on your own knowledge
                            - Always think carefully about the received content and the judgments you need to make
                            - Answers should be concise, accurate, and helpful
                            - If the user asks about weather, use the query_weather tool

                            [Decision Process]
                            1. After receiving a question, first consider if it can be answered using your existing knowledge
                            2. Include your reasoning process inside <think></think> tags
                            3. For weather queries, use the query_weather tool, e.g.: query_weather(city="Shenzhen")
                            """,
            tools=[
                ReasoningTools(add_instructions=True),
                query_weather_function  # Use the Function instance
            ],
            markdown=True,
        )
            
    def run(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Run the agent to process a query

        Args:
            prompt (str): User input prompt
            context (Optional[str]): Optional document context

        Returns:
            str: Agent response
        """
        if context:
            # RAG mode: with context
            full_prompt = f"""[Retrieved Content]\n{context}\n\n[User Question]\n{prompt}\n\nPlease answer strictly based on the [Retrieved Content]. If the question is about weather, use the query_weather tool to get real-time data."""
        else:
            # Normal chat mode: without context
            full_prompt = f"[User Question]\n{prompt}\n\nPlease provide an accurate and helpful answer. If the user asks about weather, use the query_weather tool."
        
        # Let the Agent handle the request; it will automatically decide whether to call the weather tool
        response = self.agent.run(full_prompt)
        return response.content
