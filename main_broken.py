from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import json
import httpx
import asyncio
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot Backend API", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for local LLM studio
LLM_STUDIO_ENDPOINT = "http://127.0.0.1:1234"

# HTTP client for making requests to LLM studio
http_client = httpx.AsyncClient()

# Request models
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 13107
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        body = await request.body()
        if body:
            logger.info(f"Request body: {body.decode()}")
    except:
        pass
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def root():
    # Serve the index.html file
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Chatbot Backend API is running! Navigate to /index.html to see the frontend."}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Handle chat completions requests from the frontend
    Forwards requests to local LLM studio
    """
    logger.info(f"Received chat completion request: {request}")
    try:
        # Prepare the request to forward to LLM studio
        payload = {
            "model": request.model,
            "messages": [msg.dict() for msg in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }
        
        logger.info(f"Forwarding request to LLM studio: {payload}")
        
        # For streaming responses
        if request.stream:
            return await forward_streaming_request(payload)
        
        # For regular responses
        return await forward_regular_request(payload)
        
    except Exception as e:
        logger.error(f"Error forwarding request to LLM studio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error forwarding request to LLM studio: {str(e)}")

async def forward_regular_request(payload: dict):
    """Forward a regular (non-streaming) request to LLM studio"""
    try:
        response = await http_client.post(
            f"{LLM_STUDIO_ENDPOINT}/v1/chat/completions",
            json=payload,
            timeout=30.0
        )
        
        logger.info(f"LLM studio response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"LLM studio returned error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        result = response.json()
        logger.info(f"LLM studio response: {result}")
        return result
        
    except httpx.RequestError as e:
        logger.error(f"Error connecting to LLM studio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to LLM studio: {str(e)}")

async def forward_streaming_request(payload: dict):
    """Forward a streaming request to LLM studio"""
    try:
        # Create an async generator that forwards the streaming response
        async def stream_generator():
            try:
                logger.info(f"Starting streaming request to LLM studio")
                async with http_client.stream(
                    "POST",
                    f"{LLM_STUDIO_ENDPOINT}/v1/chat/completions",
                    json=payload,
                    timeout=30.0
                ) as response:
                    logger.info(f"LLM studio streaming response status: {response.status_code}")
                    if response.status_code != 200:
                        # Yield an error message if the upstream request failed
                        error_msg = f"data: {{\\"error\\": \\"LLM studio returned status {response.status_code}\\"}}\n\n"
                        logger.error(f"LLM studio returned error: {response.status_code}")
                        yield error_msg
                        return
                    
                    # Forward each chunk as it arrives
                    async for chunk in response.aiter_text():
                        logger.info(f"Received chunk: {chunk[:100]}")  # Log first 100 chars
                        yield chunk
                        
            except httpx.RequestError as e:
                error_msg = f"data: {{\\"error\\": \\"Error connecting to LLM studio: {str(e)}\\"}}\n\n"
                logger.error(f"Error connecting to LLM studio: {str(e)}")
                yield error_msg
            except Exception as e:
                error_msg = f"data: {{\\"error\\": \\"Unexpected error: {str(e)}\\"}}\n\n"
                logger.error(f"Unexpected error: {str(e)}")
                yield error_msg
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Error setting up streaming connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting up streaming connection: {str(e)}")

# Serve static files
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)