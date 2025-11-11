"""
User Preference Agent Module

This agent is responsible for:
1. Greeting users warmly
2. Asking them about their preferences (interests, role, experience, goals)
3. Collecting and structuring their responses

Think of this agent as a friendly receptionist who gathers information
to help you find the right Discord channels.
"""

from typing import Dict, Any, List
from langsmith import traceable
import json
import logging

from agents.base_agent import BaseAgent, AgentFactory


class UserPreferenceAgent(BaseAgent):
    """
    Agent that collects user preferences through conversational interaction.
    
    This agent uses a conversational approach to gather information about:
    - User interests (topics they care about)
    - User role (their profession or position)
    - Experience level (beginner, intermediate, advanced)
    - Goals (what they want to achieve)
    
    The agent is designed to be friendly and adaptive, asking follow-up
    questions if responses are unclear.
    """
    
    # Template for the initial greeting
    GREETING_TEMPLATE = """You are a friendly assistant helping users find the best Discord channels for them.

Your task is to greet the user warmly and explain that you'll ask a few questions to understand their preferences.

Keep your greeting:
- Warm and welcoming
- Brief (2-3 sentences)
- Clear about what you'll do next

Generate only the greeting message."""

    # Template for collecting each preference
    QUESTION_TEMPLATE = """You are collecting information from a user to help them find suitable Discord channels.

You need to ask about: {field}
Question to ask: {question}
Required: {required}

Previous conversation:
{conversation_history}

Generate a natural, conversational question. If the user has already provided this information in previous responses, acknowledge it and ask for confirmation or clarification if needed."""

    # Template for validating and structuring responses
    VALIDATION_TEMPLATE = """You are analyzing a user's response to extract specific information.

Question asked: {question}
User's response: {user_response}

Extract the relevant information and return ONLY a JSON object with this structure:
{{
    "value": "the extracted information",
    "confidence": "high|medium|low",
    "needs_clarification": true|false,
    "clarification_question": "question to ask if needs_clarification is true, otherwise null"
}}

Be strict: only mark confidence as "high" if the response directly answers the question."""

    def __init__(self, name: str = "Preference Collector", 
                 model_name: str = "gpt-4", 
                 temperature: float = 0.7,
                 config: Dict[str, Any] = None):
        """
        Initialize the User Preference Agent.
        
        Args:
            name: Agent name
            model_name: LLM model to use
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
                    "question": "What's your role or profession?",
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
        
        self.conversation_history: List[Dict[str, str]] = []
        self.collected_preferences: Dict[str, Any] = {}
    
    @traceable(name="user_preference_agent_execute")
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the preference collection process.
        
        This method coordinates the entire conversation flow:
        1. Greet the user
        2. Ask each preference question
        3. Validate and store responses
        4. Return collected preferences
        
        Args:
            input_data: Dictionary with:
                - mode: "start" for initial greeting, "collect" for gathering preferences
                - user_response: (optional) User's response to the last question
                
        Returns:
            Dictionary with:
                - message: The agent's message to the user
                - status: "greeting", "collecting", or "complete"
                - preferences: Collected preferences (when complete)
        """
        mode = input_data.get('mode', 'start')
        
        if mode == 'start':
            return await self._greet_user()
        elif mode == 'collect':
            user_response = input_data.get('user_response', '')
            return await self._collect_preferences(user_response)
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    async def _greet_user(self) -> Dict[str, Any]:
        """
        Generate a warm greeting for the user.
        
        Returns:
            Dictionary with greeting message and status
        """
        self.logger.info("Generating user greeting")
        
        # Use the language model to generate a natural greeting
        response_data = await self._invoke_model(self.GREETING_TEMPLATE, return_usage=True)
        greeting = response_data['content']
        
        # Store in conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": greeting
        })
        
        return {
            "message": greeting,
            "status": "greeting",
            "next_action": "collect",
            "token_usage": {
                "prompt_tokens": response_data['usage']['prompt_tokens'],
                "completion_tokens": response_data['usage']['completion_tokens'],
                "total_tokens": response_data['usage']['total_tokens']
            }
        }
    
    async def _collect_preferences(self, user_response: str) -> Dict[str, Any]:
        """
        Collect user preferences through conversational interaction.
        
        This method handles the back-and-forth conversation, asking questions
        and validating responses.
        
        Args:
            user_response: The user's latest response
            
        Returns:
            Dictionary with next question or final preferences
        """
        # Store user's response in conversation history
        if user_response:
            self.conversation_history.append({
                "role": "user",
                "content": user_response
            })
        
        # Determine which preference we're currently collecting
        current_index = len(self.collected_preferences)
        
        # If we've collected all preferences, we're done
        if current_index >= len(self.preference_questions):
            return {
                "message": "Thank you! I have all the information I need. Let me analyze the best Discord channels for you...",
                "status": "complete",
                "preferences": self.collected_preferences
            }
        
        # Get the current question
        current_q = self.preference_questions[current_index]
        
        # If we have a user response, validate it first
        if user_response and len(self.conversation_history) > 2:
            validation_result = await self._validate_response(
                current_q['question'],
                user_response
            )
            
            # If validation failed or needs clarification
            if validation_result['needs_clarification']:
                clarification = validation_result.get('clarification_question')
                self.conversation_history.append({
                    "role": "assistant",
                    "content": clarification
                })
                return {
                    "message": clarification,
                    "status": "collecting",
                    "current_field": current_q['field']
                }
            
            # Store the validated preference
            self.collected_preferences[current_q['field']] = validation_result['value']
            self.logger.info(f"Collected preference: {current_q['field']} = {validation_result['value']}")
            
            # Move to next question
            current_index += 1
            if current_index >= len(self.preference_questions):
                return {
                    "message": "Thank you! I have all the information I need. Let me analyze the best Discord channels for you...",
                    "status": "complete",
                    "preferences": self.collected_preferences
                }
            current_q = self.preference_questions[current_index]
        
        # Generate the next question
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in self.conversation_history
        ])
        
        question_prompt = self._create_prompt(
            self.QUESTION_TEMPLATE,
            field=current_q['field'],
            question=current_q['question'],
            required="Yes" if current_q['required'] else "No",
            conversation_history=conversation_text
        )
        
        next_question = await self._invoke_model(question_prompt)
        
        self.conversation_history.append({
            "role": "assistant",
            "content": next_question
        })
        
        return {
            "message": next_question,
            "status": "collecting",
            "current_field": current_q['field']
        }
    
    async def _validate_response(self, question: str, user_response: str) -> Dict[str, Any]:
        """
        Validate a user's response to a question.
        
        This uses the language model to:
        1. Extract the relevant information from the response
        2. Determine if the response adequately answers the question
        3. Generate a clarification question if needed
        
        Args:
            question: The question that was asked
            user_response: The user's response
            
        Returns:
            Dictionary with validation results
        """
        validation_prompt = self._create_prompt(
            self.VALIDATION_TEMPLATE,
            question=question,
            user_response=user_response
        )
        
        validation_response = await self._invoke_model(validation_prompt)
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = validation_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            
            cleaned_response = cleaned_response.strip()
            
            # Parse the JSON response
            result = json.loads(cleaned_response)
            return result
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse validation response: {validation_response}")
            # If parsing fails, assume we need clarification
            return {
                "value": user_response,
                "confidence": "low",
                "needs_clarification": True,
                "clarification_question": f"I'm not sure I understood. Could you clarify: {question}"
            }
    
    def reset(self):
        """Reset the agent's state for a new conversation."""
        self.conversation_history = []
        self.collected_preferences = {}
        self.logger.info("Agent state reset")


# Register this agent with the factory
AgentFactory.register_agent('user_preference', UserPreferenceAgent)
