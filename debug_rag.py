import asyncio
import os
from dotenv import load_dotenv
from services.rag import RAGService

# Load environment variables
load_dotenv()

async def debug_rag():
    print("Initializing RAG Service...")
    try:
        service = RAGService()
        print("Service initialized.")
        
        # Check doc count
        count = service.supabase.table("documents").select("id", count="exact").execute()
        print(f"Total Documents in DB: {count.count}")
        
    except Exception as e:
        print(f"Failed to init/count: {e}")
        return

    print("Attempting to INSERT dummy doc...")
    try:
        # Check what's actually in the DB
        response = service.supabase.table("documents").select("content, metadata").limit(5).execute()
        print(f"--- DB CONTENT PEEK ({len(response.data)} rows) ---")
        for row in response.data:
            preview = row['content'][:50].replace('\n', ' ')
            meta = row['metadata']
            print(f"[{meta}] Content: {preview}...")
        print("-----------------------")

    except Exception as e:
        print(f"DB Inspection FAILED: {e}")

    print("Attempting to query knowledge base...")
    try:
        # Simple test query
        context = await service.query_knowledge_base("test")
        print(f"Query Result (Context length): {len(context)}")
        if context:
            print("Context Preview:", context[:100])
        else:
            print("No context returned. (This might be normal if DB is empty, or error if RPC is missing)")
            
    except Exception as e:
        print(f"CRITICAL RAG ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_rag())
