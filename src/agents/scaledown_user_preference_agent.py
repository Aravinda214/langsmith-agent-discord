"""
ScaleDown User Preference Agent Module

This is a ScaleDown-enabled version of the UserPreferenceAgent that uses
prompt compression to reduce token usage while collecting user preferences.

Key Differences from Standard Agent:
- Uses ScaleDown API to compress conversation history
- Tracks token savings
- Maintains same functionality and accuracy
"""

from typing import Dict, Any, List
from langsmith import traceable
import json
import logging

from agents.scaledown_base_agent import ScaleDownBaseAgent, ScaleDownAgentFactory


class ScaleDownUserPreferenceAgent(ScaleDownBaseAgent):
    """
    ScaleDown-enabled agent that collects user preferences with compression.
    
    This agent collects the same information as UserPreferenceAgent:
    - User interests
    - User role  
    - Experience level
    - Goals
    
    But uses ScaleDown to compress the conversation history before
    each LLM call, reducing token usage by 30-70%.
    """
    
    # System instruction for the agent
    SYSTEM_INSTRUCTION = """You are a friendly assistant helping users find the best Discord channels for them based on their preferences."""
    
    # Template for the initial greeting
    GREETING_CONTEXT = """The user is starting a conversation. You need to:
1. Greet them warmly
2. Explain you'll ask a few questions to understand their preferences
3. Make them feel comfortable

Keep it brief (2-3 sentences) and welcoming."""
    
    GREETING_PROMPT = "Generate a warm, welcoming greeting for the user."
    
    # Template for asking questions
    QUESTION_CONTEXT_TEMPLATE = """You are collecting preferences to recommend Discord channels.

Current field: {field}
Question to ask: {question}
Required: {required}

Conversation so far:
{conversation_history}

Guidelines:
- Ask naturally and conversationally
- If user already answered, acknowledge and ask for confirmation
- Be friendly and supportive"""
    
    QUESTION_PROMPT_TEMPLATE = "Ask the user about {field} in a natural, friendly way."
    
    # Template for validation
    VALIDATION_CONTEXT_TEMPLATE = """You are extracting structured information from a user response.

Question: {question}
User's answer: {user_response}

Your task: Extract the relevant information and assess clarity."""
    
    VALIDATION_PROMPT = """Return ONLY a JSON object with this exact structure:
{
    "value": "the extracted information",
    "confidence": "high|medium|low",
    "needs_clarification": true|false,
    "clarification_question": "question if needed, otherwise null"
}

Mark confidence as "high" only if the response directly and clearly answers the question."""
    
    def __init__(self, name: str = "ScaleDown Preference Collector", 
                 model_name: str = "gpt-4o",
                 temperature: float = 0.7,
                 config: Dict[str, Any] = None):
        """
        Initialize the ScaleDown User Preference Agent.
        
        Args:
            name: Agent name
            model_name: LLM model to use (default: gpt-4o for ScaleDown)
            temperature: Controls response creativity
            config: Configuration including preference questions
        """
        super().__init__(name, model_name, temperature, config)
        
        # Get the questions to ask from config
        self.preference_questions = config.get('preference_questions', [])
        if not self.preference_questions:
            # Default questions if none provided
            self.preference_questions = [
                {
                    "field": "interests",
                    "question": "What are your main interests or topics you'd like to discuss?",
                    "required": True
                },
                {
                    "field": "role",
                    "question": "What's your role or profession? (e.g., developer, designer, student)",
                    "required": True
                },
                {
                    "field": "experience_level",
                    "question": "What's your experience level? (beginner, intermediate, advanced)",
                    "required": True
                },
                {
                    "field": "goals",
                    "question": "What are you hoping to achieve or learn?",
                    "required": False
                }
            ]
        
        # Initialize conversation state
        self.conversation_history = []
        self.collected_preferences = {}
        
        self.logger.info(f"Initialized {self.name} with {len(self.preference_questions)} questions")
    
    @traceable(name="scaledown_collect_preferences")
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method: collect all user preferences with compression.
        
        Args:
            input_data: Can contain:
                - mode: 'greeting' | 'collect' | 'auto'
                - user_responses: List of responses (for batch mode)
                
        Returns:
            Dictionary with:
                - greeting: Initial greeting message
                - preferences: Collected preferences
                - complete: Whether collection is done
                - compression_metrics: Token usage statistics
        """
        mode = input_data.get('mode', 'auto')
        
        if mode == 'greeting':
            return await self._generate_greeting()
        elif mode == 'collect':
            user_responses = input_data.get('user_responses', [])
            return await self._collect_preferences(user_responses)
        else:  # auto mode
            greeting = await self._generate_greeting()
            return greeting
    
    @traceable(name="scaledown_generate_greeting")
    async def _generate_greeting(self) -> Dict[str, Any]:
        """
        Generate the initial greeting message using ScaleDown compression.
        
        Returns:
            Dictionary with greeting message and metrics
        """
        self.logger.info("Generating greeting with ScaleDown compression")
        
        # Use ScaleDown compression
        result = await self._invoke_model_with_compression(
            context=self.GREETING_CONTEXT,
            prompt=self.GREETING_PROMPT
        )
        
        greeting = result['response']
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': greeting
        })
        
        return {
            'greeting': greeting,
            'next_step': 'collect_preferences',
            'compression_metrics': result['compression_metrics']
        }
    
    @traceable(name="scaledown_collect_preferences")
    async def _collect_preferences(
        self, 
        user_responses: List[str] = None
    ) -> Dict[str, Any]:
        """
        Collect preferences from user with ScaleDown compression.
        
        This method goes through each question, asks the user, validates
        their response, and collects the structured data.
        
        Args:
            user_responses: Pre-provided responses (for automated testing)
            
        Returns:
            Dictionary with collected preferences and metrics
        """
        all_metrics = []
        
        for idx, question_config in enumerate(self.preference_questions):
            field = question_config['field']
            
            # Skip if already collected
            if field in self.collected_preferences:
                continue
            
            # Generate question
            question_result = await self._ask_question(question_config)
            question = question_result['question']
            all_metrics.append(question_result['compression_metrics'])
            
            print(f"\n{question}")
            
            # Get user response
            if user_responses and idx < len(user_responses):
                user_response = user_responses[idx]
                print(f"User: {user_response}")
            else:
                user_response = input("You: ")
            
            # Validate and extract
            validation_result = await self._validate_response(
                question_config['question'],
                user_response
            )
            all_metrics.append(validation_result['compression_metrics'])
            
            validation_data = validation_result['validation']
            
            # Store if confidence is high
            if validation_data['confidence'] == 'high':
                self.collected_preferences[field] = validation_data['value']
                self.logger.info(f"Collected {field}: {validation_data['value']}")
            elif validation_data['needs_clarification']:
                # Ask for clarification
                print(f"\n{validation_data['clarification_question']}")
                clarification = input("You: ")
                
                # Re-validate
                validation_result = await self._validate_response(
                    question_config['question'],
                    clarification
                )
                all_metrics.append(validation_result['compression_metrics'])
                
                validation_data = validation_result['validation']
                if validation_data['confidence'] in ['high', 'medium']:
                    self.collected_preferences[field] = validation_data['value']
        
        # Calculate aggregate metrics
        aggregate_metrics = self._aggregate_metrics(all_metrics)
        
        return {
            'preferences': self.collected_preferences,
            'complete': len(self.collected_preferences) >= len(
                [q for q in self.preference_questions if q['required']]
            ),
            'compression_metrics': aggregate_metrics,
            'conversation_history': self.conversation_history
        }
    
    async def _ask_question(self, question_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a natural question using ScaleDown compression.
        
        Args:
            question_config: Question configuration
            
        Returns:
            Dictionary with question text and metrics
        """
        # Build conversation history string
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history[-5:]  # Last 5 messages
        ])
        
        context = self.QUESTION_CONTEXT_TEMPLATE.format(
            field=question_config['field'],
            question=question_config['question'],
            required=question_config['required'],
            conversation_history=history_str if history_str else "No previous conversation"
        )
        
        prompt = self.QUESTION_PROMPT_TEMPLATE.format(
            field=question_config['field']
        )
        
        result = await self._invoke_model_with_compression(
            context=context,
            prompt=prompt
        )
        
        question = result['response']
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': question
        })
        
        return {
            'question': question,
            'compression_metrics': result['compression_metrics']
        }
    
    async def _validate_response(
        self, 
        question: str, 
        user_response: str
    ) -> Dict[str, Any]:
        """
        Validate and extract information from user response with compression.
        
        Args:
            question: The question that was asked
            user_response: User's answer
            
        Returns:
            Dictionary with validation data and metrics
        """
        self.conversation_history.append({
            'role': 'user',
            'content': user_response
        })
        
        context = self.VALIDATION_CONTEXT_TEMPLATE.format(
            question=question,
            user_response=user_response
        )
        
        result = await self._invoke_model_with_compression(
            context=context,
            prompt=self.VALIDATION_PROMPT
        )
        
        response_text = result['response'].strip()
        
        # Parse JSON response
        try:
            # Extract JSON if wrapped in markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            validation_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse validation response: {e}")
            validation_data = {
                'value': user_response,
                'confidence': 'low',
                'needs_clarification': True,
                'clarification_question': 'Could you please provide more details?'
            }
        
        return {
            'validation': validation_data,
            'compression_metrics': result['compression_metrics']
        }
    
    def _aggregate_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate compression metrics from multiple calls.
        
        Args:
            metrics_list: List of compression_metrics dictionaries
            
        Returns:
            Aggregated metrics
        """
        total_original = sum(m.get('original_tokens', 0) for m in metrics_list)
        total_compressed = sum(m.get('compressed_tokens', 0) for m in metrics_list)
        total_compression_time = sum(m.get('compression_time', 0) for m in metrics_list)
        total_llm_time = sum(m.get('llm_time', 0) for m in metrics_list)
        total_time = sum(m.get('total_time', 0) for m in metrics_list)
        
        compression_ratio = 0
        if total_original > 0:
            compression_ratio = (
                (total_original - total_compressed) / total_original * 100
            )
        
        return {
            'total_calls': len(metrics_list),
            'total_original_tokens': total_original,
            'total_compressed_tokens': total_compressed,
            'tokens_saved': total_original - total_compressed,
            'compression_ratio': compression_ratio,
            'total_compression_time': total_compression_time,
            'total_llm_time': total_llm_time,
            'total_time': total_time
        }


# Register this agent with the ScaleDown factory
ScaleDownAgentFactory.register_agent('scaledown_user_preference', ScaleDownUserPreferenceAgent)
