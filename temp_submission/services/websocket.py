"""
WebSocket connection manager for EchoSession
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from datetime import datetime
from services.database import DatabaseService
from services.llm import LLMService
from services.processor import PostSessionProcessor

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Dict[str, WebSocket] = {}
        self.db_service = DatabaseService()
        self.llm_service = LLMService()
        self.processor = PostSessionProcessor()
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """
        Accept WebSocket connection and initialize session
        
        Args:
            websocket: WebSocket connection
            session_id: Unique session identifier
            user_id: User identifier
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Create session in database
        try:
            await self.db_service.create_session(user_id, session_id)
            
            # Log system event
            await self.db_service.log_event(
                session_id=session_id,
                event_type="system_event",
                content="Session started",
                metadata={"user_id": user_id}
            )
            
            # Send welcome message
            await self.send_message(
                session_id,
                {
                    "type": "system",
                    "content": "Connected to AI assistant. How can I help you today?"
                }
            )
        except Exception as e:
            print(f"Error initializing session: {e}")
            await self.send_message(
                session_id,
                {"type": "error", "content": f"Session initialization failed: {str(e)}"}
            )
    
    async def disconnect(self, session_id: str):
        """
        Handle WebSocket disconnection and trigger post-session processing
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # Trigger post-session processing in background
        try:
            await self.processor.process_session(session_id, self.db_service, self.llm_service)
        except Exception as e:
            print(f"Error in post-session processing: {e}")
        
        # Clear LLM session from memory
        self.llm_service.clear_session(session_id)
    
    async def send_message(self, session_id: str, message: Dict):
        """
        Send message to a specific WebSocket connection
        
        Args:
            session_id: Session identifier
            message: Message dictionary to send
        """
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
    
    async def handle_message(self, session_id: str, message: str):
        """
        Handle incoming message from user
        
        Args:
            session_id: Session identifier
            message: User message
        """
        try:
            # Parse message if it's JSON
            try:
                data = json.loads(message)
                message_text = data.get("content", message)
                message_type = data.get("type", "user_message")
            except json.JSONDecodeError:
                message_text = message
                message_type = "user_message"
            
            # Log user message
            await self.db_service.log_event(
                session_id=session_id,
                event_type="user_message",
                content=message_text
            )
            
            # Check for special commands (function calling demonstration)
            if message_text.lower().startswith("/function"):
                await self.handle_function_call(session_id, message_text)
                return
            
            # Stream LLM response
            await self.stream_llm_response(session_id, message_text)
        
        except Exception as e:
            print(f"Error handling message: {e}")
            await self.send_message(
                session_id,
                {"type": "error", "content": f"Error processing message: {str(e)}"}
            )
    
    async def stream_llm_response(self, session_id: str, user_message: str):
        """
        Stream LLM response to the client
        
        Args:
            session_id: Session identifier
            user_message: User's message
        """
        full_response = ""
        
        try:
            # Send typing indicator
            await self.send_message(session_id, {"type": "typing", "content": True})
            
            # Stream response chunks
            async for chunk in self.llm_service.stream_response(session_id, user_message):
                full_response += chunk
                
                # Send chunk to client
                await self.send_message(
                    session_id,
                    {"type": "ai_response_chunk", "content": chunk}
                )
            
            # Send completion signal
            await self.send_message(session_id, {"type": "typing", "content": False})
            await self.send_message(session_id, {"type": "ai_response_complete", "content": True})
            
            # Log complete AI response
            await self.db_service.log_event(
                session_id=session_id,
                event_type="ai_response",
                content=full_response
            )
        
        except Exception as e:
            print(f"Error streaming LLM response: {e}")
            await self.send_message(
                session_id,
                {"type": "error", "content": f"Error generating response: {str(e)}"}
            )
    
    async def handle_function_call(self, session_id: str, message: str):
        """
        Handle function calling demonstration
        
        Args:
            session_id: Session identifier
            message: Function call command
        """
        try:
            # Parse function call (format: /function <function_name> <parameters>)
            parts = message.split(maxsplit=2)
            
            if len(parts) < 2:
                await self.send_message(
                    session_id,
                    {
                        "type": "system",
                        "content": "Usage: /function <function_name> [parameters]\nAvailable functions: get_weather, get_user_info, search_database"
                    }
                )
                return
            
            function_name = parts[1]
            parameters = json.loads(parts[2]) if len(parts) > 2 else {}
            
            # Log function call
            await self.db_service.log_event(
                session_id=session_id,
                event_type="function_call",
                content=f"Calling function: {function_name}",
                metadata={"function": function_name, "parameters": parameters}
            )
            
            # Execute simulated function
            result = await self.llm_service.simulate_function_call(function_name, parameters)
            
            # Send function result to user
            await self.send_message(
                session_id,
                {
                    "type": "function_result",
                    "function": function_name,
                    "result": result
                }
            )
            
            # Feed result back to LLM for interpretation
            context_message = f"Function {function_name} returned: {result['result']}"
            await self.stream_llm_response(session_id, context_message)
        
        except Exception as e:
            print(f"Error handling function call: {e}")
            await self.send_message(
                session_id,
                {"type": "error", "content": f"Function call failed: {str(e)}"}
            )
