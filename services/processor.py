"""
Post-session processor
"""
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.database import DatabaseService
    from services.llm import LLMService

class PostSessionProcessor:
    """Handles post-session processing tasks"""
    
    async def process_session(
        self,
        session_id: str,
        db_service: "DatabaseService",
        llm_service: "LLMService"
    ):
        """
        Process session after disconnection
        
        Args:
            session_id: Session identifier
            db_service: Database service instance
            llm_service: LLM service instance
        """
        try:
            print(f"Starting post-session processing for session: {session_id}")
            
            # Get session data
            session = await db_service.get_session(session_id)
            if not session:
                print(f"Session {session_id} not found")
                return
            
            # Get all events for this session
            events = await db_service.get_session_events(session_id)
            
            if not events:
                print(f"No events found for session {session_id}")
                # Update session with end time only
                end_time = datetime.utcnow()
                
                try:
                    start_time_str = session["start_time"]
                    if start_time_str.endswith('Z'):
                        start_time_str = start_time_str.replace('Z', '+00:00')
                    start_time = datetime.fromisoformat(start_time_str)
                except (ValueError, KeyError):
                    start_time = end_time
                
                duration = int((end_time - start_time.replace(tzinfo=None) if start_time.tzinfo else end_time - start_time).total_seconds())
                
                await db_service.update_session(
                    session_id=session_id,
                    end_time=end_time,
                    duration_seconds=duration,
                    session_summary="No conversation occurred in this session."
                )
                return
            
            # Generate AI summary of the conversation
            print(f"Analyzing {len(events)} events for session {session_id}")
            summary = await llm_service.analyze_conversation(events)
            
            # Calculate session duration
            end_time = datetime.utcnow()
            
            # Robust date parsing from ISO format
            try:
                start_time_str = session["start_time"]
                # Handle 'Z' suffix for UTC and other common ISO variations
                if start_time_str.endswith('Z'):
                    start_time_str = start_time_str.replace('Z', '+00:00')
                start_time = datetime.fromisoformat(start_time_str)
            except (ValueError, KeyError) as e:
                print(f"Error parsing start_time for session {session_id}: {e}")
                start_time = end_time # Fallback to prevent crash
                
            duration_seconds = int((end_time - start_time.replace(tzinfo=None) if start_time.tzinfo else end_time - start_time).total_seconds())
            
            # Update session with summary and end time
            await db_service.update_session(
                session_id=session_id,
                end_time=end_time,
                duration_seconds=duration_seconds,
                session_summary=summary
            )
            
            # Log completion
            await db_service.log_event(
                session_id=session_id,
                event_type="system_event",
                content="Session ended and summary generated",
                metadata={
                    "duration_seconds": duration_seconds,
                    "event_count": len(events)
                }
            )
            
            print(f"Post-session processing completed for session: {session_id}")
        
        except Exception as e:
            print(f"Error in post-session processing: {e}")
            # Still try to update end time even if summary generation fails
            try:
                end_time = datetime.utcnow()
                await db_service.update_session(
                    session_id=session_id,
                    end_time=end_time,
                    session_summary=f"Summary generation failed: {str(e)}"
                )
            except Exception as update_error:
                print(f"Failed to update session end time: {update_error}")
