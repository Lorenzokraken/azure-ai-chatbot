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
from dotenv import dotenv_values
from db.db import get_db

# Carica variabili d'ambiente
env_vars = dotenv_values(".env")
AZURE_API_KEY = env_vars.get("AZURE_API_KEY")
AZURE_ENDPOINT = env_vars.get("AZURE_ENDPOINT")
AZURE_DEPLOYMENT_NAME = env_vars.get("AZURE_DEPLOYMENT_NAME")
OPENROUTER_API_KEY = env_vars.get("OPENROUTER_API_KEY")

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KrakenGPT API", version="1.0.0")

# Initialize database
db = get_db()

# CORS (aggiorna in produzione)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelli supportati per Azure
AZURE_SUPPORTED_MODELS = [
    "gpt-35-turbo",  # Azure model name
    "gpt-4",         # Azure model name
    "gpt-4.1",       # Azure model name
]

# Modelli supportati per OpenRouter (modelli free)
OPENROUTER_SUPPORTED_MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-7b-it:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "openchat/openchat-7b:free",
    "neversleep/llama-3-lumimaid-8b:free",
    "sao10k/fimbulvetr-11b-v2:free"
]

# Provider configuration
DEFAULT_PROVIDER = "azure"  # Default provider
SUPPORTED_PROVIDERS = ["azure", "openrouter"]

logger.info(f"Azure API key configured: {'Yes' if AZURE_API_KEY else 'No'}")
logger.info(f"Azure endpoint configured: {'Yes' if AZURE_ENDPOINT else 'No'}")
logger.info(f"OpenRouter API key configured: {'Yes' if OPENROUTER_API_KEY else 'No'}")
http_client = httpx.AsyncClient(timeout=30.0)

# Modelli Pydantic
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 13107
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

# Project and Chat models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ChatCreate(BaseModel):
    project_id: Optional[int] = None
    title: str
    messages: Optional[List[Dict[str, Any]]] = []
    context: Optional[str] = ""

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    context: Optional[str] = None

class ChatCompletionRequestWithChat(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 13107
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    chat_id: Optional[int] = None  # Optional chat ID to associate with existing chat
    provider: Optional[str] = DEFAULT_PROVIDER  # Provider selection (azure or openrouter)

# Middleware per log
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the database when the application starts."""
    db.init_database()
    logger.info("Database initialized")
    
    # Create a default project if none exists
    projects = db.get_all_projects()
    if not projects:
        default_project_id = db.create_project("Default Project", "Default project for chatbot")
        logger.info(f"Created default project with ID: {default_project_id}")

# Endpoint base
@app.get("/")
async def root():
    return FileResponse("index.html") if os.path.exists("index.html") else {"message": "Running!"}

@app.get("/models")
async def get_models():
    return {
        "providers": SUPPORTED_PROVIDERS,
        "default_provider": DEFAULT_PROVIDER,
        "models": {
            "azure": AZURE_SUPPORTED_MODELS,
            "openrouter": OPENROUTER_SUPPORTED_MODELS
        }
    }

# Project endpoints
@app.post("/api/projects")
def create_project(project: ProjectCreate):
    """Create a new project."""
    project_id = db.create_project(project.name, project.description)
    if not project_id:
        raise HTTPException(status_code=400, detail="Project already exists")
    return {"id": project_id, "name": project.name, "description": project.description}

@app.get("/api/projects")
def get_projects():
    """Get all projects."""
    return db.get_all_projects()

@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    """Get a specific project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/api/projects/{project_id}")
def update_project(project_id: int, project: ProjectUpdate):
    """Update a project."""
    success = db.update_project(
        project_id, 
        name=project.name, 
        description=project.description
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project updated successfully"}

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int):
    """Delete a project."""
    success = db.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

# Chat endpoints
@app.post("/api/chats")
def create_chat(chat: ChatCreate):
    """Create a new chat."""
    chat_id = db.create_chat(chat.project_id, chat.title, chat.messages, chat.context)
    if not chat_id:
        raise HTTPException(status_code=400, detail="Failed to create chat. Project may not exist.")
    new_chat = db.get_chat(chat_id)
    return new_chat

@app.get("/api/projects/{project_id}/chats")
def get_chats_for_project(project_id: int):
    """Get all chats for a project."""
    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return db.get_chats_by_project(project_id)

@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: int):
    """Get a specific chat."""
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.put("/api/chats/{chat_id}")
def update_chat(chat_id: int, chat: ChatUpdate):
    """Update a chat."""
    success = db.update_chat(
        chat_id,
        title=chat.title,
        messages=chat.messages,
        context=chat.context
    )
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    updated_chat = db.get_chat(chat_id)
    return updated_chat

@app.delete("/api/chats/{chat_id}")
def delete_chat_api(chat_id: int):
    """Delete a chat."""
    success = db.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequestWithChat):
    # Validate provider
    provider = request.provider or DEFAULT_PROVIDER
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    # Check if required API keys are available based on provider
    if provider == "azure" and (not AZURE_API_KEY or not AZURE_ENDPOINT):
        # Fallback to OpenRouter if Azure is not configured
        if OPENROUTER_API_KEY:
            provider = "openrouter"
            logger.info("Falling back to OpenRouter as Azure is not configured")
        else:
            raise HTTPException(status_code=500, detail="No provider configured. Please set Azure or OpenRouter API keys.")
    
    if provider == "openrouter" and not OPENROUTER_API_KEY:
        # If OpenRouter is not configured and we're trying to use it, fallback to Azure
        if AZURE_API_KEY and AZURE_ENDPOINT:
            provider = "azure"
            logger.info("Falling back to Azure as OpenRouter is not configured")
        else:
            raise HTTPException(status_code=500, detail="No provider configured. Please set Azure or OpenRouter API keys.")
    
    payload = {
        "messages": [msg.dict() for msg in request.messages],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "stream": request.stream
    }
    
    try:
        if provider == "azure":
            # For Azure, we need to extract the deployment name from the model string
            deployment_name = request.model
            
            # Construct Azure endpoint URL
            url = f"{AZURE_ENDPOINT}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
            
            if request.stream:
                return await forward_azure_streaming_request(payload, request.chat_id, request.messages, deployment_name)
            else:
                return await forward_azure_regular_request(payload, request.chat_id, request.messages, deployment_name)
                
        elif provider == "openrouter":
            # For OpenRouter, use the model directly
            payload["model"] = request.model
            
            # Construct OpenRouter endpoint URL
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            if request.stream:
                return await forward_openrouter_streaming_request(payload, request.chat_id, request.messages)
            else:
                return await forward_openrouter_regular_request(payload, request.chat_id, request.messages)
                
    except Exception as e:
        logger.error(f"Error with {provider}: {str(e)}")
        # Try fallback if one provider fails
        if provider == "azure" and OPENROUTER_API_KEY:
            logger.info("Falling back to OpenRouter due to Azure error")
            try:
                payload["model"] = request.model
                url = "https://openrouter.ai/api/v1/chat/completions"
                
                if request.stream:
                    return await forward_openrouter_streaming_request(payload, request.chat_id, request.messages)
                else:
                    return await forward_openrouter_regular_request(payload, request.chat_id, request.messages)
            except Exception as fallback_error:
                logger.error(f"OpenRouter fallback also failed: {str(fallback_error)}")
                raise HTTPException(status_code=500, detail=f"Both providers failed: {str(e)} | {str(fallback_error)}")
        elif provider == "openrouter" and AZURE_API_KEY and AZURE_ENDPOINT:
            logger.info("Falling back to Azure due to OpenRouter error")
            try:
                deployment_name = request.model
                url = f"{AZURE_ENDPOINT}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
                
                if request.stream:
                    return await forward_azure_streaming_request(payload, request.chat_id, request.messages, deployment_name)
                else:
                    return await forward_azure_regular_request(payload, request.chat_id, request.messages, deployment_name)
            except Exception as fallback_error:
                logger.error(f"Azure fallback also failed: {str(fallback_error)}")
                raise HTTPException(status_code=500, detail=f"Both providers failed: {str(e)} | {str(fallback_error)}")
        else:
            raise HTTPException(status_code=500, detail=str(e))

# Azure request handlers
async def forward_azure_regular_request(payload: dict, chat_id: Optional[int], messages: List[Message], deployment_name: str):
    # Construct Azure endpoint URL
    url = f"{AZURE_ENDPOINT}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    
    try:
        response = await http_client.post(
            url,
            json=payload,
            headers={
                "api-key": AZURE_API_KEY,
                "Content-Type": "application/json"
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        # Get the response data
        response_data = response.json()
        
        # Store the conversation in the database if chat_id is provided
        if chat_id:
            # Get existing chat
            chat = db.get_chat(chat_id)
            if chat:
                # Update chat with new messages
                existing_messages = chat.get("messages", [])
                # Add user messages
                for msg in messages:
                    existing_messages.append({"role": msg.role, "content": msg.content})
                # Add AI response
                ai_message = response_data["choices"][0]["message"]
                existing_messages.append({"role": ai_message["role"], "content": ai_message["content"]})
                # Update chat in database
                db.update_chat(chat_id, messages=existing_messages)
        
        return response_data
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Azure connection error: {str(e)}")

async def forward_azure_streaming_request(payload: dict, chat_id: Optional[int], messages: List[Message], deployment_name: str):
    # Construct Azure endpoint URL
    url = f"{AZURE_ENDPOINT}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    
    async def stream_generator():
        full_response = ""
        try:
            async with http_client.stream(
                "POST",
                url,
                json=payload,
                headers={
                    "api-key": AZURE_API_KEY,
                    "Content-Type": "application/json"
                }
            ) as response:
                if response.status_code != 200:
                    yield f'data: {{"error": "Azure error: Status {response.status_code}"}}\n\n'
                    return
                
                # Store user messages if chat_id is provided
                if chat_id:
                    chat = db.get_chat(chat_id)
                    if chat:
                        existing_messages = chat.get("messages", [])
                        # Add user messages
                        for msg in messages:
                            existing_messages.append({"role": msg.role, "content": msg.content})
                        # Update chat in database
                        db.update_chat(chat_id, messages=existing_messages)
                
                async for chunk in response.aiter_text():
                    # Try to extract content from the chunk for storage
                    if chat_id and chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                        try:
                            # Parse the JSON data
                            if chunk.strip() != "data: [DONE]":
                                data = json.loads(chunk[6:])  # Remove "data: " prefix
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        full_response += delta["content"]
                        except:
                            pass  # Ignore parsing errors for streaming
                    
                    yield chunk
                
                # Store the full AI response if chat_id is provided
                if chat_id and full_response:
                    chat = db.get_chat(chat_id)
                    if chat:
                        existing_messages = chat.get("messages", [])
                        # Add AI response
                        existing_messages.append({"role": "assistant", "content": full_response})
                        # Update chat in database
                        db.update_chat(chat_id, messages=existing_messages)
                        
        except Exception as e:
            yield f'data: {{"error": "Azure streaming error: {str(e)}"}}\n\n'

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# OpenRouter request handlers
async def forward_openrouter_regular_request(payload: dict, chat_id: Optional[int], messages: List[Message]):
    try:
        response = await http_client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "KrakenGPT"
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        # Get the response data
        response_data = response.json()
        
        # Store the conversation in the database if chat_id is provided
        if chat_id:
            # Get existing chat
            chat = db.get_chat(chat_id)
            if chat:
                # Update chat with new messages
                existing_messages = chat.get("messages", [])
                # Add user messages
                for msg in messages:
                    existing_messages.append({"role": msg.role, "content": msg.content})
                # Add AI response
                ai_message = response_data["choices"][0]["message"]
                existing_messages.append({"role": ai_message["role"], "content": ai_message["content"]})
                # Update chat in database
                db.update_chat(chat_id, messages=existing_messages)
        
        return response_data
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"OpenRouter connection error: {str(e)}")

async def forward_openrouter_streaming_request(payload: dict, chat_id: Optional[int], messages: List[Message]):
    async def stream_generator():
        full_response = ""
        try:
            async with http_client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "KrakenGPT"
                }
            ) as response:
                if response.status_code != 200:
                    yield f'data: {{"error": "OpenRouter error: Status {response.status_code}"}}\n\n'
                    return
                
                # Store user messages if chat_id is provided
                if chat_id:
                    chat = db.get_chat(chat_id)
                    if chat:
                        existing_messages = chat.get("messages", [])
                        # Add user messages
                        for msg in messages:
                            existing_messages.append({"role": msg.role, "content": msg.content})
                        # Update chat in database
                        db.update_chat(chat_id, messages=existing_messages)
                
                async for chunk in response.aiter_text():
                    # Try to extract content from the chunk for storage
                    if chat_id and chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                        try:
                            # Parse the JSON data
                            if chunk.strip() != "data: [DONE]":
                                data = json.loads(chunk[6:])  # Remove "data: " prefix
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        full_response += delta["content"]
                        except:
                            pass  # Ignore parsing errors for streaming
                    
                    yield chunk
                
                # Store the full AI response if chat_id is provided
                if chat_id and full_response:
                    chat = db.get_chat(chat_id)
                    if chat:
                        existing_messages = chat.get("messages", [])
                        # Add AI response
                        existing_messages.append({"role": "assistant", "content": full_response})
                        # Update chat in database
                        db.update_chat(chat_id, messages=existing_messages)
                        
        except Exception as e:
            yield f'data: {{"error": "OpenRouter streaming error: {str(e)}"}}\n\n'

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# Monta static files
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)