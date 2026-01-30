-- Session Metadata Table
CREATE TABLE session_metadata (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    session_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Event Log Table
CREATE TABLE event_log (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES session_metadata(session_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- 'user_message', 'ai_response', 'function_call', 'system_event'
    content TEXT NOT NULL,
    metadata JSONB, -- Additional context (function name, parameters, etc.)
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient querying
CREATE INDEX idx_event_log_session ON event_log(session_id, timestamp);

-- Optional: Index for user queries
CREATE INDEX idx_session_user ON session_metadata(user_id, start_time DESC);
