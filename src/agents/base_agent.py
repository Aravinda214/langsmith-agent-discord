"""
Base Agent Module

This module defines the abstract base class for all agents in the system.
It provides a common interface and shared functionality that all agents must implement.

Key Concepts:
- Abstract Base Class (ABC): A template that other classes inherit from
- LangSmith Integration: Automatic tracking of agent interactions for debugging
- Type Hints: Makes code more readable and catches errors early
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langsmith import traceable
import logging


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    This class provides the foundation that all specialized agents build upon.
    Think of it as a blueprint - it defines WHAT methods agents need, but not HOW they work.
    Each specific agent (like UserPreferenceAgent) will provide the HOW.
    
    Attributes:
        name (str): The agent's display name
        model (ChatOpenAI): The language model used by the agent
        config (Dict): Configuration settings for the agent
        logger (Logger): For logging agent activities
    """
    
    def __init__(self, name: str, model_name: str = "gpt-4", 
                 temperature: float = 0.7, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: Display name for the agent
            model_name: Which OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
            temperature: Controls randomness (0.0 = focused, 1.0 = creative)
            config: Additional configuration options
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize the language model
        # This is the "brain" of the agent - it processes language and generates responses
        self.model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=self.config.get('max_tokens', 500)
        )
        
        self.logger.info(f"Initialized {self.name} with model {model_name}")
    
    @abstractmethod
    @traceable(name="agent_execute")
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        
        This is an abstract method - it MUST be implemented by each specific agent.
        The @abstractmethod decorator enforces this requirement.
        
        The @traceable decorator automatically sends execution data to LangSmith,
        allowing you to see what the agent did, how long it took, and any errors.
        
        Args:
            input_data: Dictionary containing the input for the agent
            
        Returns:
            Dictionary containing the agent's output
            
        Raises:
            NotImplementedError: If a subclass doesn't implement this method
        """
        pass
    
    def _create_prompt(self, template: str, **kwargs) -> str:
        """
        Helper method to create formatted prompts.
        
        Prompts are instructions we give to the language model.
        This method uses Python's string formatting to fill in variables.
        
        Args:
            template: A string with placeholders like {variable_name}
            **kwargs: The values to fill in the placeholders
            
        Returns:
            The formatted prompt string
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"Missing required variable in prompt template: {e}")
            raise
    
    async def _invoke_model(self, prompt: str) -> str:
        """
        Send a prompt to the language model and get a response.
        
        This is a wrapper around the model's invoke method that adds
        error handling and logging.
        
        Args:
            prompt: The instruction/question for the model
            
        Returns:
            The model's text response
        """
        try:
            self.logger.debug(f"Invoking model with prompt: {prompt[:100]}...")
            response = await self.model.ainvoke(prompt)
            return response.content
        except Exception as e:
            self.logger.error(f"Error invoking model: {e}")
            raise
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "model": self.model.model_name,
            "temperature": self.model.temperature
        }


class AgentFactory:
    """
    Factory pattern for creating agents.
    
    The Factory pattern is a design pattern that provides a centralized way
    to create objects. Instead of creating agents directly with their constructors,
    we use this factory. This makes it easier to:
    - Add new agent types without changing existing code
    - Configure agents from a central location
    - Swap agent implementations easily
    
    Think of it like a car factory - you tell it what type of car you want,
    and it builds it for you according to the specifications.
    """
    
    _agent_registry: Dict[str, type] = {}
    
    @classmethod
    def register_agent(cls, agent_type: str, agent_class: type):
        """
        Register a new agent type.
        
        This allows the factory to create instances of this agent type.
        
        Args:
            agent_type: String identifier for the agent (e.g., "preference_collector")
            agent_class: The class to instantiate (e.g., UserPreferenceAgent)
        """
        cls._agent_registry[agent_type] = agent_class
        logging.info(f"Registered agent type: {agent_type}")
    
    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> BaseAgent:
        """
        Create an agent instance.
        
        Args:
            agent_type: The type of agent to create
            **kwargs: Arguments to pass to the agent's constructor
            
        Returns:
            An instance of the requested agent type
            
        Raises:
            ValueError: If the agent type is not registered
        """
        if agent_type not in cls._agent_registry:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available types: {list(cls._agent_registry.keys())}"
            )
        
        agent_class = cls._agent_registry[agent_type]
        logging.info(f"Creating agent of type: {agent_type}")
        return agent_class(**kwargs)
    
    @classmethod
    def list_agent_types(cls) -> list:
        """Get a list of all registered agent types."""
        return list(cls._agent_registry.keys())
