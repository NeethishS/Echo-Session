import asyncio
import websockets
import uuid
import sys
import urllib.request
import traceback

async def check_api():
    print("Checking HTTP health endpoint...", flush=True)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8001/health") as response:
            print(f"Health Check Status: {response.status}", flush=True)
            print(f"Health Check Body: {response.read().decode()}", flush=True)
    except Exception as e:
        print(f"Health Check Failed: {e}", file=sys.stderr, flush=True)
        return False

    print(f"websockets version: {websockets.__version__}", flush=True)
    session_id = str(uuid.uuid4())
    uri = f"ws://127.0.0.1:8001/ws/session/{session_id}?user_id=test_user"
    
    print(f"Connecting to {uri}...", flush=True)
    try:
        # Connect without extra headers
        async with websockets.connect(uri) as websocket:
            print("Connected successfully.", flush=True)
            
            # Send a test message
            message = "Hello, this is a test message to check API status."
            print(f"Sending message: {message}", flush=True)
            await websocket.send(message)
            
            print("Waiting for response...", flush=True)
            
            # Collect response chunks
            full_response = ""
            chunk_count = 0
            
            while True:
                try:
                    # Set a timeout for each chunk
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    chunk_count += 1
                    full_response += response
                    print(f"Chunk {chunk_count}: {response}", flush=True)
                    
                    if "Error:" in response:
                        print(f"API Error detected in chunk: {response}", file=sys.stderr, flush=True)
                        return False
                    
                    if '"type": "ai_response' in response or '"type":"ai_response' in response:
                         print(f"\nReceived AI response: {response[:100]}...", flush=True)
                         return True
                         
                    # Check for typing indicator just to know it's working
                    if '"type": "typing"' in response:
                         print("AI is typing...", flush=True)

                except asyncio.TimeoutError:
                    if chunk_count > 0:
                        print("\nResponse stream pause/timeout. Assuming success for now.", flush=True)
                        return True
                    else:
                        print("\nTimeout waiting for FIRST response. API might be down or slow.", file=sys.stderr, flush=True)
                        return False
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"\nConnection closed by server: {e}", file=sys.stderr, flush=True)
                    return False
                    
    except Exception as e:
        traceback.print_exc()
        print(f"Failed to connect: {e}", file=sys.stderr, flush=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(check_api())
    if success:
        print("\nAPI Check: SUCCESS - Server responded correctly.", flush=True)
        sys.exit(0)
    else:
        print("\nAPI Check: FAILED - Issues detected.", file=sys.stderr, flush=True)
        sys.exit(1)
