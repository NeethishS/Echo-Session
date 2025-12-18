# EchoSession

Asynchronous Python backend for real-time AI conversations.

## Quick Start

1. Set up Supabase database (run `database_schema.sql`)
2. Configure `.env` file with credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`
5. Open: `http://localhost:8000`

## Technology

- FastAPI (WebSocket server)
- Groq API (LLM - Llama 3.3 70B)
- Supabase (PostgreSQL database)

## Features

- Real-time WebSocket communication
- LLM streaming (Groq - Llama 3.3)sponses
- Conversation logging
- Post-session analysis
- Function calling demo

## Environment Variables

```
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
GROQ_API_KEY=your_key
```

## Database Schema

Two tables:
- `session_metadata` - Session info and summaries
- `event_log` - Detailed conversation events

See `database_schema.sql` for full schema.

## API Endpoints

- `GET /` - Frontend interface
- `GET /health` - Health check
- `WS /ws/session/{session_id}` - WebSocket endpoint
- `GET /api/session/{session_id}` - Get session data
- `GET /api/session/{session_id}/events` - Get session events

## Project Structure

```
├── main.py              # FastAPI app
├── config.py            # Configuration
├── services/
│   ├── database.py      # Supabase client
│   ├── llm.py          # Groq integration
│   ├── websocket.py    # Connection manager
│   └── processor.py    # Post-session processing
└── static/
    └── index.html      # Frontend
```

## Testing

1. Start server
2. Open browser to `http://localhost:8000`
3. Click "Connect to Session"
4. Send messages
5. Try function calling buttons
6. Disconnect and check Supabase for summary

## Troubleshooting

**Server won't start:**
- Check `.env` file exists and has correct values
- Verify virtual environment is activated

**WebSocket connection fails:**
- Ensure server is running
- Check browser console for errors

**No database entries:**
- Verify Supabase credentials
- Check database schema was created
- Look at server logs for errors
