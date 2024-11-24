"""
Asynchronous agent implementation for the GRAMI framework.

This module provides the main asynchronous agent implementation, which is the
recommended way to use GRAMI in modern applications.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Union, List, Callable
import asyncio
import json
from datetime import datetime
import uuid

from .base import BaseAgent
from ..core.base import BaseLLMProvider


class AsyncAgent(BaseAgent):
    """
    Asynchronous agent implementation with streaming and memory capabilities.
    
    This is the primary agent class for GRAMI, providing full asynchronous
    support for message handling, streaming responses, and memory management.
    """
    
    async def send_message(
        self,
        message: Union[str, Dict[str, str]],
        context: Optional[Dict] = None
    ) -> str:
        """
        Send a message and get a response asynchronously.
        
        Args:
            message: Message content (string or role-content dictionary)
            context: Optional context information
            
        Returns:
            Response from the LLM
        
        Raises:
            Exception: If there's an error in message processing
        """
        try:
            # Normalize message format
            message_payload = self._normalize_message(message)
            
            # Add message to memory if available
            if self.memory:
                await self.memory.add_message(message_payload)
            
            # Send message with context
            response = await self.llm.send_message(
                message_payload,
                **(context or {})
            )
            
            # Store response in memory if available
            if self.memory:
                await self.memory.add_message({
                    "role": "model",
                    "content": response
                })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in send_message: {str(e)}")
            raise
    
    async def stream_message(
        self,
        message: Union[str, Dict[str, str]],
        context: Optional[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a message response asynchronously.
        
        Args:
            message: Message content (string or role-content dictionary)
            context: Optional context information
            **kwargs: Additional keyword arguments for the LLM
            
        Yields:
            Response tokens from the LLM
            
        Raises:
            Exception: If there's an error in message streaming
        """
        try:
            # Normalize message format
            message_payload = self._normalize_message(message)
            
            # Add message to memory if available
            if self.memory:
                await self.memory.add_message(message_payload)
            
            # Initialize response storage for memory
            response_chunks = []
            
            # Stream response
            async for chunk in self.llm.stream_message(
                message_payload,
                **(context or {}),
                **kwargs
            ):
                response_chunks.append(chunk)
                yield chunk
            
            # Store complete response in memory if available
            if self.memory:
                await self.memory.add_message({
                    "role": "model",
                    "content": "".join(response_chunks)
                })
                
        except Exception as e:
            self.logger.error(f"Error in stream_message: {str(e)}")
            raise
    
    @classmethod
    async def setup_communication(
        cls,
        communication_type: str = 'websocket',
        host: str = 'localhost',
        port: int = 8765,
        path: str = '/ws'
    ):
        """
        Set up a communication interface for the agent.
        
        Args:
            communication_type: Type of communication interface
            host: Host address for the server
            port: Port number for the server
            path: WebSocket path
            
        Returns:
            Configured communication interface
        """
        if communication_type == 'websocket':
            from ..communication.websocket import WebSocketInterface
            return await WebSocketInterface.create(host=host, port=port, path=path)
        else:
            raise ValueError(f"Unsupported communication type: {communication_type}")