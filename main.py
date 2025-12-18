"""
EchoSession - Main FastAPI application
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uuid
import os
import config
from services.websocket import ConnectionManager

# Validate configuration on startup
config.validate_config()

# Initialize FastAPI app
app = FastAPI(
    title="EchoSession",
    description="WebSocket AI conversation system",
    version="1.0.0"
)

# Initialize connection manager
manager = ConnectionManager()

@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "EchoSession",
        "version": "1.0.0"
    }

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversation
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier (UUID format recommended)
    """
    # Validate session_id format
    try:
        uuid.UUID(session_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid session_id format. Must be a valid UUID.")
        return
    
    # Get user_id from query parameters (in production, this would come from authentication)
    user_id = websocket.query_params.get("user_id", "anonymous")
    
    await manager.connect(websocket, session_id, user_id)
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            
            # Handle the message
            await manager.handle_message(session_id, message)
    
    except WebSocketDisconnect:
        print(f"Client disconnected from session: {session_id}")
        await manager.disconnect(session_id)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(session_id)

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session metadata
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session metadata including summary if available
    """
    try:
        session = await manager.db_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}/events")
async def get_session_events(session_id: str):
    """
    Get all events for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of events
    """
    try:
        events = await manager.db_service.get_session_events(session_id)
        return {"session_id": session_id, "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (for serving HTML/CSS/JS)
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        print("Static files mounted successfully from /static")
    else:
        print("Warning: 'static' directory not found. Frontend may not load.")
except Exception as e:
    print(f"Error mounting static files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
