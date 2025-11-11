"""
ScaleDown Base Agent Module

This module defines an alternative base class for agents that use ScaleDown API
for prompt compression before sending to the LLM. This reduces token usage and costs
while maintaining accuracy.

Key Features:
- Prompt compression using ScaleDown API
- Token usage tracking for comparison
- LangSmith integration for monitoring
- Compatible with existing agent architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langsmith import traceable
import logging
import requests
import json
import time
import os


class ScaleDownBaseAgent(ABC):
    """
    Abstract base class for agents using ScaleDown prompt compression.
    
    This agent follows a 3-step process:
    1. Compress the context and prompt using ScaleDown API
    2. Create final prompt with compressed context
    3. Send to OpenAI with reduced token usage
    
    Benefits:
    - Reduced token consumption (30-70% typical reduction)
    - Lower API costs
    - Faster response times
    - Maintains accuracy
    
    Attributes:
        name (str): The agent's display name
        model (ChatOpenAI): The language model used by the agent
        config (Dict): Configuration settings for the agent
        logger (Logger): For logging agent activities
        scaledown_api_key (str): ScaleDown API key
        scaledown_url (str): ScaleDown API endpoint
        compression_stats (Dict): Tracks compression metrics
    """
    
    def __init__(self, name: str, model_name: str = "gpt-4o", 
                 temperature: float = 0.7, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ScaleDown base agent.
        
        Args:
            name: Display name for the agent
            model_name: Which OpenAI model to use (default: "gpt-4o")
            temperature: Controls randomness (0.0 = focused, 1.0 = creative)
            config: Additional configuration options including scaledown settings
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # ScaleDown API configuration
        self.scaledown_api_key = os.getenv('SCALEDOWN_API_KEY')
        if not self.scaledown_api_key:
            self.logger.warning("SCALEDOWN_API_KEY not found in environment variables")
        
        self.scaledown_url = self.config.get(
            'scaledown_url', 
            'https://api.scaledown.xyz/compress/raw/'
        )
        
        # Compression settings
        self.compression_rate = self.config.get('compression_rate', 'auto')
        
        # Initialize the language model
        self.model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=self.config.get('max_tokens', 500)
        )
        
        # Track compression statistics
        self.compression_stats = {
            'total_calls': 0,
            'total_original_tokens': 0,
            'total_compressed_tokens': 0,
            'total_compression_time': 0,
            'total_llm_time': 0,
            'compression_failures': 0
        }
        
        self.logger.info(
            f"Initialized {self.name} with ScaleDown compression "
            f"(model: {model_name}, rate: {self.compression_rate})"
        )
    
    @abstractmethod
    @traceable(name="scaledown_agent_execute")
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task with ScaleDown compression.
        
        This is an abstract method - it MUST be implemented by each specific agent.
        
        Args:
            input_data: Dictionary containing the input for the agent
            
        Returns:
            Dictionary containing the agent's output including compression metrics
        """
        pass
    
    @traceable(name="scaledown_compress")
    async def _compress_with_scaledown(
        self, 
        context: str, 
        prompt: str, 
        model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """
        Compress context and prompt using ScaleDown API.
        
        This is Step 1 of the 3-step process. It sends your long context
        and question to ScaleDown, which intelligently compresses it while
        preserving the important information.
        
        Args:
            context: Long context information (this gets compressed)
            prompt: The actual question/instruction (also compressed)
            model: Target model for compression optimization
            
        Returns:
            Dictionary with:
                - compressed_prompt: The compressed text
                - original_tokens: Estimated tokens before compression
                - compressed_tokens: Estimated tokens after compression
                - compression_ratio: Percentage of reduction
                - compression_time: Time taken to compress
        """
        if not self.scaledown_api_key:
            raise ValueError(
                "SCALEDOWN_API_KEY not set. Please add it to your .env file"
            )
        
        start_time = time.time()
        
        headers = {
            'x-api-key': self.scaledown_api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "context": context,
            "prompt": prompt,  # Send both context and prompt to ScaleDown
            "model": model,
            "scaledown": {
                "rate": self.compression_rate
            }
        }
        
        try:
            self.logger.debug(f"Compressing with ScaleDown (rate: {self.compression_rate})")
            
            response = requests.post(
                self.scaledown_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            compression_time = time.time() - start_time
            
            # Extract compression metrics from nested 'results' object
            results_data = result.get('results', {})
            compressed_prompt = results_data.get('compressed_prompt', '')
            original_tokens = results_data.get('original_prompt_tokens', 0)
            compressed_tokens = results_data.get('compressed_prompt_tokens', 0)
            
            # Calculate compression ratio
            if original_tokens > 0:
                compression_ratio = (
                    (original_tokens - compressed_tokens) / original_tokens * 100
                )
            else:
                compression_ratio = 0
            
            self.logger.info(
                f"Compression successful: {original_tokens} → {compressed_tokens} tokens "
                f"({compression_ratio:.1f}% reduction) in {compression_time:.2f}s"
            )
            
            # Update stats
            self.compression_stats['total_calls'] += 1
            self.compression_stats['total_original_tokens'] += original_tokens
            self.compression_stats['total_compressed_tokens'] += compressed_tokens
            self.compression_stats['total_compression_time'] += compression_time
            
            return {
                'compressed_prompt': compressed_prompt,
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'compression_ratio': compression_ratio,
                'compression_time': compression_time,
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ScaleDown API error: {e}")
            self.compression_stats['compression_failures'] += 1
            
            # Fallback: return uncompressed
            return {
                'compressed_prompt': f"{context}\n\n{prompt}",
                'original_tokens': 0,
                'compressed_tokens': 0,
                'compression_ratio': 0,
                'compression_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    @traceable(name="scaledown_invoke_model")
    async def _invoke_model_with_compression(
        self, 
        context: str, 
        prompt: str
    ) -> Dict[str, Any]:
        """
        Complete 3-step process: Compress, format, and invoke LLM.
        
        Step 1: Compress context and prompt with ScaleDown
        Step 2: Create final prompt with compressed context
        Step 3: Send to OpenAI and get response
        
        Args:
            context: Long background information
            prompt: The actual question/instruction
            
        Returns:
            Dictionary with:
                - response: The LLM's text response
                - compression_metrics: Token usage and compression stats
                - total_time: End-to-end time
        """
        overall_start = time.time()
        
        # Step 1: Compress with ScaleDown
        compression_result = await self._compress_with_scaledown(
            context=context,
            prompt=prompt,
            model=self.model.model_name
        )
        
        if not compression_result['success']:
            self.logger.warning(f"Compression failed: {compression_result.get('error', 'Unknown error')}")
        
        compressed_prompt = compression_result['compressed_prompt']
        
        # Step 2: Build final prompt following ScaleDown's recommended pattern
        # Wrap compressed context with system instructions and re-state the question
        final_prompt = f"""System: You are a helpful assistant that answers questions using the provided context.

Context: {compressed_prompt}

User: {prompt}

Please provide a clear and accurate response based on the context above."""
        
        # Step 3: Send to OpenAI
        try:
            llm_start = time.time()
            self.logger.debug("Invoking LLM with compressed prompt")
            
            response = await self.model.ainvoke(final_prompt)
            llm_time = time.time() - llm_start
            
            self.compression_stats['total_llm_time'] += llm_time
            
            total_time = time.time() - overall_start
            
            self.logger.info(
                f"LLM response received in {llm_time:.2f}s "
                f"(total: {total_time:.2f}s), response length: {len(response.content)}"
            )
            
            if not response.content or len(response.content.strip()) == 0:
                self.logger.warning("LLM returned empty response!")
            
            return {
                'response': response.content,
                'compression_metrics': {
                    'original_tokens': compression_result['original_tokens'],
                    'compressed_tokens': compression_result['compressed_tokens'],
                    'compression_ratio': compression_result['compression_ratio'],
                    'compression_time': compression_result['compression_time'],
                    'llm_time': llm_time,
                    'total_time': total_time,
                    'compression_success': compression_result['success']
                },
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error invoking model: {e}")
            return {
                'response': '',
                'compression_metrics': compression_result,
                'success': False,
                'error': str(e)
            }
    
    def _create_prompt(self, template: str, **kwargs) -> str:
        """
        Helper method to create formatted prompts.
        
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
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent including compression stats.
        
        Returns:
            Dictionary with agent metadata and performance metrics
        """
        stats = self.compression_stats.copy()
        
        # Calculate averages
        if stats['total_calls'] > 0:
            stats['avg_compression_ratio'] = (
                (stats['total_original_tokens'] - stats['total_compressed_tokens']) 
                / stats['total_original_tokens'] * 100
            )
            stats['avg_compression_time'] = (
                stats['total_compression_time'] / stats['total_calls']
            )
            stats['avg_llm_time'] = (
                stats['total_llm_time'] / stats['total_calls']
            )
        else:
            stats['avg_compression_ratio'] = 0
            stats['avg_compression_time'] = 0
            stats['avg_llm_time'] = 0
        
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "model": self.model.model_name,
            "temperature": self.model.temperature,
            "uses_compression": True,
            "compression_rate": self.compression_rate,
            "compression_stats": stats
        }
    
    def get_compression_summary(self) -> str:
        """
        Get a human-readable summary of compression performance.
        
        Returns:
            Formatted string with compression statistics
        """
        info = self.get_info()
        stats = info['compression_stats']
        
        if stats['total_calls'] == 0:
            return "No compression calls made yet."
        
        return f"""
ScaleDown Compression Summary for {self.name}
{'=' * 50}
Total API Calls: {stats['total_calls']}
Compression Failures: {stats['compression_failures']}

Token Usage:
  Original Tokens: {stats['total_original_tokens']:,}
  Compressed Tokens: {stats['total_compressed_tokens']:,}
  Tokens Saved: {stats['total_original_tokens'] - stats['total_compressed_tokens']:,}
  Avg Compression: {stats['avg_compression_ratio']:.1f}%

Performance:
  Total Compression Time: {stats['total_compression_time']:.2f}s
  Total LLM Time: {stats['total_llm_time']:.2f}s
  Avg Compression Time: {stats['avg_compression_time']:.3f}s
  Avg LLM Time: {stats['avg_llm_time']:.3f}s
"""


class ScaleDownAgentFactory:
    """
    Factory pattern for creating ScaleDown agents.
    
    Similar to the standard AgentFactory but for ScaleDown-enabled agents.
    """
    
    _agent_registry: Dict[str, type] = {}
    
    @classmethod
    def register_agent(cls, agent_type: str, agent_class: type):
        """
        Register a new ScaleDown agent type.
        
        Args:
            agent_type: String identifier (e.g., "scaledown_preference")
            agent_class: The class to instantiate
        """
        cls._agent_registry[agent_type] = agent_class
        logging.info(f"Registered ScaleDown agent type: {agent_type}")
    
    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> ScaleDownBaseAgent:
        """
        Create a ScaleDown agent instance.
        
        Args:
            agent_type: The type of agent to create
            **kwargs: Arguments to pass to the agent's constructor
            
        Returns:
            An instance of the requested agent type
        """
        if agent_type not in cls._agent_registry:
            raise ValueError(
                f"Unknown ScaleDown agent type: {agent_type}. "
                f"Available types: {list(cls._agent_registry.keys())}"
            )
        
        agent_class = cls._agent_registry[agent_type]
        logging.info(f"Creating ScaleDown agent of type: {agent_type}")
        return agent_class(**kwargs)
    
    @classmethod
    def list_agent_types(cls) -> list:
        """Get a list of all registered ScaleDown agent types."""
        return list(cls._agent_registry.keys())
