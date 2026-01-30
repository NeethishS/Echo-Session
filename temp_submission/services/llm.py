"""
LLM service for Groq API integration
"""
from groq import Groq
from typing import AsyncGenerator, Dict, Any, List, Optional
import config

# Initialize Groq client
client = Groq(api_key=config.GROQ_API_KEY)

class LLMService:
    """Service for managing LLM interactions with Groq"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = client
        self.chat_sessions: Dict[str, List[Dict]] = {}
    
    def get_or_create_chat(self, session_id: str, system_prompt: Optional[str] = None) -> List[Dict]:
        """
        Get existing chat history or create a new one
        
        Args:
            session_id: Session identifier
            system_prompt: Optional system prompt for the chat
            
        Returns:
            Chat history
        """
        if session_id not in self.chat_sessions:
            history = []
            if system_prompt:
                history.append({
                    "role": "system",
                    "content": system_prompt
                })
            self.chat_sessions[session_id] = history
        
        return self.chat_sessions[session_id]
    
    async def stream_response(
        self,
        session_id: str,
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response for a user message
        
        Args:
            session_id: Session identifier
            user_message: User's message
            system_prompt: Optional system prompt
            
        Yields:
            Chunks of the LLM response
        """
        try:
            history = self.get_or_create_chat(session_id, system_prompt)
            
            # Add user message to history
            history.append({
                "role": "user",
                "content": user_message
            })
            
            # Stream response from Groq
            stream = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history,
                stream=True,
                temperature=0.7,
                max_tokens=1024
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add assistant response to history
            history.append({
                "role": "assistant",
                "content": full_response
            })
        
        except Exception as e:
            print(f"Error streaming LLM response: {e}")
            yield f"Error: {str(e)}"
    
    async def get_full_response(
        self,
        session_id: str,
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Get complete LLM response (non-streaming)
        
        Args:
            session_id: Session identifier
            user_message: User's message
            system_prompt: Optional system prompt
            
        Returns:
            Complete LLM response
        """
        try:
            history = self.get_or_create_chat(session_id, system_prompt)
            
            history.append({
                "role": "user",
                "content": user_message
            })
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history,
                temperature=0.7,
                max_tokens=1024
            )
            
            assistant_message = response.choices[0].message.content
            
            history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return f"Error: {str(e)}"
    
    async def analyze_conversation(self, events: List[Dict[str, Any]]) -> str:
        """
        Analyze conversation history and generate a summary
        
        Args:
            events: List of conversation events
            
        Returns:
            AI-generated session summary
        """
        try:
            # Build conversation history
            conversation_text = "Conversation History:\n\n"
            for event in events:
                event_type = event.get("event_type", "")
                content = event.get("content", "")
                
                if event_type == "user_message":
                    conversation_text += f"User: {content}\n"
                elif event_type == "ai_response":
                    conversation_text += f"AI: {content}\n"
                elif event_type == "function_call":
                    conversation_text += f"[Function Call: {content}]\n"
            
            # Generate summary
            prompt = f"""{conversation_text}

Please provide a concise summary of this conversation session. Include:
1. Main topics discussed
2. Key questions asked by the user
3. Important information provided
4. Overall conversation outcome

Keep the summary brief (3-5 sentences)."""
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error analyzing conversation: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def clear_session(self, session_id: str):
        """
        Clear chat session from memory
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
    
    async def simulate_function_call(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a function call (for demonstration purposes)
        
        Args:
            function_name: Name of the function to call
            parameters: Function parameters
            
        Returns:
            Simulated function result
        """
        simulated_functions = {
            "get_weather": {
                "result": "The weather is sunny with a temperature of 72°F",
                "data": {"temperature": 72, "condition": "sunny"}
            },
            "get_user_info": {
                "result": "User information retrieved successfully",
                "data": {"name": "Test User", "email": "user@example.com"}
            },
            "search_database": {
                "result": "Found 5 matching records",
                "data": {"count": 5, "records": ["Record 1", "Record 2", "Record 3"]}
            }
        }
        
        return simulated_functions.get(
            function_name,
            {"result": f"Function {function_name} executed", "data": parameters}
        )
