import os
from typing import List, Dict, Any
from fastapi import UploadFile
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from io import BytesIO
from supabase import create_client, Client
import json
import config

class RAGService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    async def ingest_document(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process uploaded file: Read -> Split -> Embed -> Store
        """
        content = ""
        filename = file.filename

        # 1. Read File
        if filename.endswith(".pdf"):
            pdf_bytes = await file.read()
            reader = PdfReader(BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    # Clean text: remove excessive whitespace/newlines
                    # Some PDFs extract as "H e l l o", we might need more advanced cleaning but for now just standard normalization
                    clean_text = " ".join(text.split())
                    content += clean_text + "\n"
        else:
            # Assume text/markdown
            content_bytes = await file.read()
            content = content_bytes.decode('utf-8')
        
        print(f"--- INGESTION DEBUG ---")
        print(f"Filename: {filename}")
        print(f"Extracted Length: {len(content)}")
        print(f"Content Preview: {content[:100]}...")
        print(f"-----------------------")

        if not content.strip():
            raise ValueError("Empty document")

        # 2. Split Text (Simple chunking by paragraphs or size)
        chunks = self._chunk_text(content)
        
        # 3. Generate Embeddings & Store
        stored_chunks = 0
        for chunk in chunks:
            embedding = self.model.encode(chunk).tolist()
            
            data = {
                "content": chunk,
                "metadata": {"filename": filename},
                "embedding": embedding
            }
            
            try:
                self.supabase.table("documents").insert(data).execute()
                stored_chunks += 1
            except Exception as e:
                print(f"Error storing chunk: {e}")

        return {
            "filename": filename,
            "chunks_processed": stored_chunks,
            "message": "Document successfully ingested into Knowledge Base."
        }

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Simple text splitting strategy"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_length += len(word) + 1
            current_chunk.append(word)
            
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    async def query_knowledge_base(self, query: str) -> str:
        """
        Search for relevant context for a query
        """
        # 1. Embed Query
        query_embedding = self.model.encode(query).tolist()
        
        # 2. Search Database (RPC call to Supabase)
        # Note: 'match_documents' function must be created in Supabase SQL
        # Fallback: exact match is hard, vector match requires RPC.
        # Since I can't create RPC easily without user SQL, I'll try standard vector select if library supports it,
        # OR just rely on the 'match_documents' RPC convention which is standard.
        
        try:
            # This relies on a 'match_documents' postgres function existing.
            # If user didn't run the RPC sql, this fails.
            # Workaround: Fetch top items (inefficient without RPC) or Assume standard RPC name.
            # I'll try the standard RPC approach first.
            response = self.supabase.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.1, # Lowered from 0.5
                    "match_count": 3
                }
            ).execute()
            
            context = ""
            for item in response.data:
                context += f"{item['content']}\n---\n"
            
            return context
            
        except Exception as e:
            print(f"Vector search failed (RPC missing?): {e}")
            return ""

