import google.generativeai as genai
from typing import Any, Dict, List, Optional
import uuid
import logging

from grami_ai.memory.memory import AbstractMemory

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Default model and configuration for Gemini
DEFAULT_MODEL_NAME = "gemini-1.5-flash-8b"  # Or another suitable model
DEFAULT_SYSTEM_INSTRUCTION = "You Are Called Grami, an Expert Digital Media agent, responsible for Plan, Create, Schedule, and Grow Instagram accounts, use tools when you can"


class GeminiAPI:
    def __init__(
            self,
            api_key: str,
            model_name: str = DEFAULT_MODEL_NAME,
            system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
            memory: Optional[AbstractMemory] = None,
            safety_settings: Optional[List[Dict[str, str]]] = None,
            generation_config: Optional[genai.GenerationConfig] = None,
            tools: Optional[list] = None,  # Add tools parameter
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.memory = memory
        self.chat_id = None
        self.model = None
        self.convo = None  # Conversation object
        self.safety_settings = safety_settings
        self.generation_config = generation_config
        self.tools = tools

        genai.configure(api_key=self.api_key)

    def initialize_chat(self):
        """Initializes the chat session and model, starting a new conversation."""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings,
            generation_config=self.generation_config,
            tools=self.tools,  # Pass tools to the model
        )
        self.convo = self.model.start_chat(enable_automatic_function_calling=True)
        self.chat_id = str(uuid.uuid4())
        logger.info(f"Initialized chat with model {self.model_name}, chat ID: {self.chat_id}")

    async def send_message(self, message: str, chat_id: str = None) -> str:
        """
        Sends a message in the chat session, creating a new conversation if none exists.
        """
        # Initialize chat if no conversation exists
        if not self.convo or (chat_id and self.chat_id != chat_id):
            self.initialize_chat()
            self.chat_id = chat_id or self.chat_id

        # Load chat history from memory if available
        if self.memory:
            history = await self.memory.get_items(self.chat_id)
            self.convo.history = self.transform_history_for_gemini(history)

        # Send the message
        response = self.convo.send_message(message)

        # Store messages in memory
        if self.memory:
            await self.memory.add_item(self.chat_id, {"role": "user", "content": message})
            await self.memory.add_item(self.chat_id, {"role": "model", "content": response.text})

        return response.text

    def transform_history_for_gemini(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transforms conversation history to the format required by Gemini."""
        return [{"role": msg["role"], "parts": [{"text": msg["content"]}]} for msg in history]
