"""
Database service for Supabase
"""
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, List, Dict, Any
import config

class DatabaseService:
    """Service for managing Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    async def create_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Create a new session in the database
        
        Args:
            user_id: User identifier
            session_id: Unique session identifier
            
        Returns:
            Created session data
        """
        try:
            data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.utcnow().isoformat(),
            }
            
            response = self.client.table("session_metadata").insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
    
    async def log_event(
        self,
        session_id: str,
        event_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log an event to the event_log table
        
        Args:
            session_id: Session identifier
            event_type: Type of event (user_message, ai_response, function_call, system_event)
            content: Event content
            metadata: Additional metadata (optional)
            
        Returns:
            Created event data
        """
        try:
            data = {
                "session_id": session_id,
                "event_type": event_type,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            response = self.client.table("event_log").insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error logging event: {e}")
            raise
    
    async def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a session, ordered by timestamp
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of events
        """
        try:
            response = (
                self.client.table("event_log")
                .select("*")
                .eq("session_id", session_id)
                .order("timestamp", desc=False)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Error fetching session events: {e}")
            raise
    
    async def update_session(
        self,
        session_id: str,
        end_time: Optional[datetime] = None,
        duration_seconds: Optional[int] = None,
        session_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update session metadata
        
        Args:
            session_id: Session identifier
            end_time: Session end time
            duration_seconds: Session duration in seconds
            session_summary: AI-generated session summary
            
        Returns:
            Updated session data
        """
        try:
            update_data = {}
            
            if end_time:
                update_data["end_time"] = end_time.isoformat()
            if duration_seconds is not None:
                update_data["duration_seconds"] = duration_seconds
            if session_summary:
                update_data["session_summary"] = session_summary
            
            response = (
                self.client.table("session_metadata")
                .update(update_data)
                .eq("session_id", session_id)
                .execute()
            )
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error updating session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """

        try:
            response = (
                self.client.table("session_metadata")
                .select("*")
                .eq("session_id", session_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching session: {e}")
            raise