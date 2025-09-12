from fastapi import FastAPI, HTTPException, Request, UploadFile, File
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

# Import RAG Service
from rag_simple import rag

# Carica variabili d'ambiente
env_vars = dotenv_values(".env")
AZURE_API_KEY = env_vars.get("AZURE_API_KEY")
AZURE_ENDPOINT = env_vars.get("AZURE_ENDPOINT")
AZURE_DEPLOYMENT_NAME = env_vars.get("AZURE_DEPLOYMENT_NAME")
OPENROUTER_API_KEY = env_vars.get("OPENROUTER_API_KEY")
OPENROUTER_MODELS_ENDPOINT = env_vars.get("OPENROUTER_MODELS", "https://openrouter.ai/api/v1/models")
LOCAL_ENDPOINT = env_vars.get("LOCAL_ENDPOINT", "http://localhost:1234/v1/chat/completions")
LOCAL_MODEL = env_vars.get("LOCAL_MODEL", "qwen/qwen3-4b-thinking-2507")

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

# Modelli supportati per OpenRouter (modelli free testati)
OPENROUTER_SUPPORTED_MODELS = [
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-haiku",
    "meta-llama/llama-3.1-8b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free"
]

# Funzione per caricare i modelli OpenRouter dinamicamente
async def load_openrouter_models():
    """Carica i modelli disponibili da OpenRouter API"""
    if not OPENROUTER_API_KEY:
        return OPENROUTER_SUPPORTED_MODELS
    
    try:
        response = await http_client.get(
            OPENROUTER_MODELS_ENDPOINT,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "KrakenGPT"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model in data.get("data", []):
                model_id = model.get("id", "")
                # Filtra solo i modelli gratuiti (con ":free" o pricing con free_tokens > 0)
                pricing = model.get("pricing", {})
                is_free = (
                    ":free" in model_id.lower() or 
                    pricing.get("completion") == "0" or
                    pricing.get("prompt") == "0"
                )
                
                if is_free:
                    models.append(model_id)
            
            logger.info(f"Caricati {len(models)} modelli gratuiti da OpenRouter")
            return models if models else OPENROUTER_SUPPORTED_MODELS
        else:
            logger.warning(f"Errore caricamento modelli OpenRouter: {response.status_code}")
            return OPENROUTER_SUPPORTED_MODELS
            
    except Exception as e:
        logger.error(f"Errore nella richiesta modelli OpenRouter: {e}")
        return OPENROUTER_SUPPORTED_MODELS

# Modelli supportati per Local (caricati dinamicamente da LM Studio)

# Funzione per caricare i modelli locali dinamicamente
async def load_local_models():
    """Carica i modelli disponibili da LM Studio"""
    try:
        # Prova a recuperare i modelli da LM Studio
        response = await http_client.get(
            "http://localhost:1234/v1/models",
            timeout=5.0
        )
        
        if response.status == 200:
            data = response.json()
            models = []
            
            # LM Studio restituisce una lista di modelli
            if isinstance(data, list):
                for model in data:
                    if isinstance(model, dict) and 'id' in model:
                        models.append(model['id'])
                    elif isinstance(model, str):
                        models.append(model)
            
            if models:
                logger.info(f"Caricati {len(models)} modelli locali da LM Studio")
                return models
        
        # Se non riusciamo a caricare, restituiamo un messaggio di errore
        logger.warning(f"Errore caricamento modelli locali: {response.status if 'response' in locals() else 'No response'}")
        return ["Apri LM Studio per caricare i modelli locali"]
        
    except Exception as e:
        logger.error(f"Errore nella richiesta modelli locali: {e}")
        return ["Apri LM Studio per caricare i modelli locali"]

# Provider configuration
DEFAULT_PROVIDER = "azure"  # Default provider
SUPPORTED_PROVIDERS = ["azure", "openrouter", "local"]

logger.info(f"Azure API key configured: {'Yes' if AZURE_API_KEY else 'No'}")
logger.info(f"Azure endpoint configured: {'Yes' if AZURE_ENDPOINT else 'No'}")
logger.info(f"OpenRouter API key configured: {'Yes' if OPENROUTER_API_KEY else 'No'}")
logger.info(f"Local endpoint configured: {LOCAL_ENDPOINT}")
logger.info(f"Local model configured: {LOCAL_MODEL}")
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
    # Carica dinamicamente i modelli OpenRouter
    openrouter_models = await load_openrouter_models()
    
    # Carica dinamicamente i modelli locali da LM Studio
    local_models = await load_local_models()
    
    return {
        "providers": SUPPORTED_PROVIDERS,
        "default_provider": DEFAULT_PROVIDER,
        "models": {
            "azure": AZURE_SUPPORTED_MODELS,
            "openrouter": openrouter_models,
            "local": local_models
        }
    }

@app.get("/providers")
async def get_providers():
    """Get available providers with their configuration status"""
    providers_status = []
    
    for provider in SUPPORTED_PROVIDERS:
        status = {
            "name": provider,
            "display_name": provider.title(),
            "available": False,
            "models": []
        }
        
        if provider == "azure":
            status["available"] = bool(AZURE_API_KEY and AZURE_ENDPOINT)
            status["models"] = AZURE_SUPPORTED_MODELS
            status["description"] = "Microsoft Azure OpenAI Service"
        elif provider == "openrouter":
            status["available"] = bool(OPENROUTER_API_KEY)
            status["models"] = await load_openrouter_models()
            status["description"] = "OpenRouter AI (Free models)"
        elif provider == "local":
            status["available"] = bool(LOCAL_ENDPOINT)
            status["models"] = await load_local_models()
            status["description"] = "Local AI Server"
        
        providers_status.append(status)
    
    return {
        "providers": providers_status,
        "default_provider": DEFAULT_PROVIDER
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

# RAG Endpoints - Document upload and management
@app.post("/api/projects/{project_id}/upload-doc")
async def upload_document(project_id: int, file: UploadFile = File(...)):
    """Upload documento TXT per RAG (versione essenziale)"""
    
    # Verifica progetto esiste
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Solo TXT per versione essenziale
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Solo file .txt supportati in questa versione")
    
    try:
        # Leggi contenuto file
        content = await file.read()
        text = content.decode('utf-8')
        
        if len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="File troppo piccolo (minimo 50 caratteri)")
        
        # Processa con RAG Service
        logger.info(f"📄 Processando documento {file.filename} per progetto {project_id}")
        doc_id = rag.add_document(project_id, file.filename, text)
        
        # Ottieni statistiche aggiornate
        stats = rag.get_project_stats(project_id)
        
        return {
            "message": f"✅ Documento {file.filename} caricato con successo", 
            "doc_id": doc_id,
            "filename": file.filename,
            "stats": stats
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Errore lettura file: assicurati che sia UTF-8")
    except Exception as e:
        logger.error(f"❌ Errore upload {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Errore processamento: {str(e)}")

@app.get("/api/projects/{project_id}/documents")
def get_documents(project_id: int):
    """Lista documenti RAG del progetto"""
    
    # Verifica progetto esiste
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Ottieni documenti con conteggio chunks
        cursor.execute('''
            SELECT 
                rd.id, rd.filename, rd.created_at,
                COUNT(rc.id) as chunk_count,
                LENGTH(rd.content) as content_size
            FROM rag_documents rd
            LEFT JOIN rag_chunks rc ON rd.id = rc.document_id
            WHERE rd.project_id = ?
            GROUP BY rd.id
            ORDER BY rd.created_at DESC
        ''', (project_id,))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "id": row[0],
                "filename": row[1], 
                "created_at": row[2],
                "chunk_count": row[3],
                "content_size": row[4]
            })
        
        # Ottieni statistiche generali
        stats = rag.get_project_stats(project_id)
        
        return {
            "documents": documents,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Errore recupero documenti: {e}")
        raise HTTPException(status_code=500, detail="Errore recupero documenti")
    finally:
        conn.close()

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int):
    """Elimina documento RAG e tutti i suoi chunks"""
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica documento esiste
        cursor.execute('SELECT filename FROM rag_documents WHERE id = ?', (document_id,))
        doc = cursor.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento non trovato")
        
        filename = doc[0]
        
        # Elimina chunks (CASCADE dovrebbe gestirlo automaticamente)
        cursor.execute('DELETE FROM rag_chunks WHERE document_id = ?', (document_id,))
        
        # Elimina documento
        cursor.execute('DELETE FROM rag_documents WHERE id = ?', (document_id,))
        
        conn.commit()
        
        logger.info(f"🗑️ Documento {filename} eliminato (ID: {document_id})")
        return {"message": f"Documento {filename} eliminato con successo"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Errore eliminazione documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore eliminazione documento")
    finally:
        conn.close()

@app.post("/api/rag/search")
def rag_search(request: dict):
    """Test endpoint per ricerca RAG"""
    
    query = request.get('query')
    project_id = request.get('project_id')
    
    if not query or not project_id:
        raise HTTPException(status_code=400, detail="Query e project_id richiesti")
    
    try:
        # Esegui ricerca RAG
        context = rag.search(query, project_id)
        stats = rag.get_project_stats(project_id)
        
        return {
            "query": query,
            "context": context,
            "context_length": len(context),
            "has_results": len(context) > 0,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Errore ricerca RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Errore ricerca: {str(e)}")

def enhance_text_with_markdown(text: str) -> str:
    """
    Migliora un testo aggiungendo markdown automaticamente se il modello non lo ha fatto
    """
    if not text:
        return text
    
    # Controlla se il testo ha già markdown (presenza di marcatori comuni)
    markdown_indicators = ['**', '*', '`', '#', '##', '###', '-', '1.', '>', '```']
    has_markdown = any(indicator in text for indicator in markdown_indicators)
    
    if has_markdown:
        return text  # Il testo ha già markdown, non modificare
    
    # Post-processing automatico per aggiungere markdown
    lines = text.split('\n')
    enhanced_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            enhanced_lines.append('')
            continue
            
        # Riconosci domande/titoli (linee che finiscono con :)
        if line.endswith(':') and len(line) > 10:
            enhanced_lines.append(f"### {line}")
        # Riconosci liste (linee che iniziano con -, •, o numeri)
        elif line.startswith(('- ', '• ', '* ')) or (len(line) > 3 and line[0].isdigit() and line[1:3] in ['. ', ') ']):
            enhanced_lines.append(line)
        # Riconosci termini tecnici (parole in MAIUSCOLO o con estensioni file)
        elif any(word.isupper() and len(word) > 2 for word in line.split()) or any(ext in line.lower() for ext in ['.py', '.js', '.css', '.html', '.json']):
            # Wrap parole tecniche in backticks
            words = line.split()
            enhanced_words = []
            for word in words:
                if (word.isupper() and len(word) > 2) or any(ext in word.lower() for ext in ['.py', '.js', '.css', '.html', '.json']):
                    enhanced_words.append(f"`{word}`")
                else:
                    enhanced_words.append(word)
            enhanced_lines.append(' '.join(enhanced_words))
        else:
            # Aggiungi enfasi a parole importanti comuni
            important_words = ['importante', 'attenzione', 'nota', 'errore', 'successo', 'warning', 'error']
            for word in important_words:
                if word.lower() in line.lower():
                    line = line.replace(word, f"**{word}**")
                    line = line.replace(word.capitalize(), f"**{word.capitalize()}**")
            enhanced_lines.append(line)
    
    return '\n'.join(enhanced_lines)

@app.delete("/api/chats/{chat_id}")
def delete_chat_api(chat_id: int):
    """Delete a chat."""
    success = db.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequestWithChat):
    """Chat endpoint potenziato con RAG automatico"""
    
    # DEBUG: Log della richiesta
    logger.info(f"🎯 Chat completions request - chat_id: {request.chat_id}")
    
    # 🧠 RAG INTEGRATION - Ricerca automatica del context
    rag_context = ""
    rag_used = False
    
    # Estrai ultima query utente per RAG
    user_query = ""
    if request.messages:
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if user_messages:
            user_query = user_messages[-1].content
            logger.info(f"🗣️ User query estratta: '{user_query[:100]}...'")
    
    # Se c'è chat_id e query, cerca context RAG
    if request.chat_id and user_query.strip():
        try:
            logger.info(f"🔍 Tentativo ricerca RAG per chat_id: {request.chat_id}")
            chat = db.get_chat(request.chat_id)
            logger.info(f"📁 Chat trovata: {chat}")
            
            if chat and chat.get('project_id'):
                project_id = chat['project_id']
                logger.info(f"📂 Project ID: {project_id}")
                
                # Verifica se ci sono documenti per questo progetto
                stats = rag.get_project_stats(project_id)
                logger.info(f"📊 Stats RAG: {stats}")
                
                if stats['documents'] > 0:
                    logger.info(f"🔍 Ricerca RAG per query: '{user_query[:50]}...'")
                    rag_context = rag.search(user_query, project_id)
                    
                    if rag_context:
                        rag_used = True
                        logger.info(f"✅ RAG attivato: {len(rag_context)} caratteri di context")
                        logger.info(f"🧠 Context preview: {rag_context[:200]}...")
                    else:
                        logger.info("📭 RAG: nessun context rilevante trovato")
                else:
                    logger.info("📭 Nessun documento trovato per questo progetto")
            else:
                logger.info("❌ Chat non trovata o senza project_id")
        except Exception as e:
            logger.error(f"⚠️ Errore RAG (continuando senza): {e}")
    else:
        logger.info(f"❌ Condizioni RAG non soddisfatte - chat_id: {request.chat_id}, query: '{user_query[:50] if user_query else 'VUOTA'}'")
    
    # Costruisci messages con RAG context se disponibile
    messages_to_send = []
    
    # System message potenziato con RAG
    base_system = """You are KrakenGPT, a powerful AI assistant focused on providing helpful, accurate responses.

CORE PRINCIPLES:
- PRIORITIZE the current user message over conversation history
- Respond directly to what the user is asking RIGHT NOW
- Don't let previous context override the current question
- If asked "who are you", respond about yourself regardless of previous topics

CRITICAL FORMATTING REQUIREMENTS:
- ALWAYS use markdown formatting in your responses
- Use **bold** for important terms
- Use `code` for technical terms, filenames, and commands
- Use ### headings to organize sections
- Use bullet points (- item) for lists
- Use numbered lists (1. item) when order matters
- Use > quotes for quotations
- Use ```language for code blocks
- NEVER respond in plain text - ALWAYS include markdown formatting

RESPONSE STRATEGY:
- Read the LATEST user message carefully
- Answer EXACTLY what they're asking now
- Use conversation history only for relevant context, not to override current intent
- Be direct, helpful, and properly formatted with markdown"""
    
    if rag_used and rag_context:
        enhanced_system = f"""{base_system}

🔍 **CONTEXTUAL INFORMATION AVAILABLE**
You have access to relevant information from the user's documents. Use this ONLY when it helps answer their CURRENT question.

--- RETRIEVED CONTEXT ---
{rag_context}
--- END CONTEXT ---

ENHANCED RESPONSE INSTRUCTIONS:
- FIRST: Focus on answering the user's current question directly
- SECOND: Use the context above ONLY if it's relevant to their current question
- Provide specific information from documents when it helps
- If context doesn't relate to current question, ignore it and answer normally
- MANDATORY: Format response with proper markdown (headings, bold, lists, code blocks)
- Structure answer with clear sections using ### headings
- Stay focused on the user's immediate need, not past conversation topics"""
        
        logger.info("🧠 RAG System message attivo")
    else:
        enhanced_system = base_system
    
    # Costruisci lista messaggi finale
    original_messages = [msg.dict() for msg in request.messages]
    
    # Rimuovi eventuali system messages esistenti
    user_messages = [msg for msg in original_messages if msg['role'] != 'system']
    
    # Aggiungi system message potenziato
    messages_to_send = [{"role": "system", "content": enhanced_system}] + user_messages
    
    # Validate provider
    provider = request.provider or DEFAULT_PROVIDER
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    # Check if required API keys/endpoints are available based on provider
    if provider == "azure" and (not AZURE_API_KEY or not AZURE_ENDPOINT):
        # Fallback to Local first, then OpenRouter if Azure is not configured
        if LOCAL_ENDPOINT:
            provider = "local"
            logger.info("Falling back to Local as Azure is not configured")
        elif OPENROUTER_API_KEY:
            provider = "openrouter"
            logger.info("Falling back to OpenRouter as Azure and Local are not configured")
        else:
            raise HTTPException(status_code=500, detail="No provider configured. Please set Azure, Local, or OpenRouter settings.")
    
    if provider == "openrouter" and not OPENROUTER_API_KEY:
        # Fallback to Local first, then Azure if OpenRouter is not configured
        if LOCAL_ENDPOINT:
            provider = "local"
            logger.info("Falling back to Local as OpenRouter is not configured")
        elif AZURE_API_KEY and AZURE_ENDPOINT:
            provider = "azure"
            logger.info("Falling back to Azure as OpenRouter and Local are not configured")
        else:
            raise HTTPException(status_code=500, detail="No provider configured. Please set Azure, Local, or OpenRouter settings.")
    
    if provider == "local" and not LOCAL_ENDPOINT:
        # Fallback to Azure first, then OpenRouter if Local is not configured
        if AZURE_API_KEY and AZURE_ENDPOINT:
            provider = "azure"
            logger.info("Falling back to Azure as Local is not configured")
        elif OPENROUTER_API_KEY:
            provider = "openrouter"
            logger.info("Falling back to OpenRouter as Local and Azure are not configured")
        else:
            raise HTTPException(status_code=500, detail="No provider configured. Please set Azure, Local, or OpenRouter settings.")
    
    payload = {
        "messages": messages_to_send,  # Usa messaggi con RAG
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
        
        elif provider == "local":
            # For Local, use the model directly
            payload["model"] = request.model
            
            if request.stream:
                return await forward_local_streaming_request(payload, request.chat_id, request.messages)
            else:
                return await forward_local_regular_request(payload, request.chat_id, request.messages)
                
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
        
        # Apply markdown enhancement to AI response
        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_message = response_data["choices"][0]["message"]
            enhanced_content = enhance_text_with_markdown(ai_message["content"])
            response_data["choices"][0]["message"]["content"] = enhanced_content
        
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
                # Add AI response (already enhanced)
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
        logger.info(f"OpenRouter request - Model: {payload.get('model')}, Payload: {payload}")
        response = await http_client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "KrakenGPT"
            }
        )
        logger.info(f"OpenRouter response status: {response.status_code}")
        if response.status_code == 401:
            raise HTTPException(
                status_code=401, 
                detail="❌ OpenRouter API key non valida o scaduta. Verifica le credenziali in OpenRouter."
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404, 
                detail=f"❌ Modello '{payload.get('model')}' non trovato su OpenRouter. Verifica che il modello sia disponibile."
            )
        elif response.status_code != 200:
            error_detail = f"OpenRouter Error {response.status_code}: {response.text}"
            raise HTTPException(status_code=response.status_code, detail=error_detail)
        
        # Get the response data
        response_data = response.json()
        
        # Apply markdown enhancement to AI response
        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_message = response_data["choices"][0]["message"]
            enhanced_content = enhance_text_with_markdown(ai_message["content"])
            response_data["choices"][0]["message"]["content"] = enhanced_content
        
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
                # Add AI response (already enhanced)
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

# Local provider request handlers
async def forward_local_regular_request(payload: dict, chat_id: Optional[int], messages: List[Message]):
    try:
        response = await http_client.post(
            LOCAL_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json"
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        # Get the response data
        response_data = response.json()
        
        # Apply markdown enhancement to AI response
        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_message = response_data["choices"][0]["message"]
            enhanced_content = enhance_text_with_markdown(ai_message["content"])
            response_data["choices"][0]["message"]["content"] = enhanced_content
        
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
                # Add AI response (already enhanced)
                ai_message = response_data["choices"][0]["message"]
                existing_messages.append({"role": ai_message["role"], "content": ai_message["content"]})
                # Update chat in database
                db.update_chat(chat_id, messages=existing_messages)
        
        return response_data
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Local connection error: {str(e)}")

async def forward_local_streaming_request(payload: dict, chat_id: Optional[int], messages: List[Message]):
    async def stream_generator():
        full_response = ""
        try:
            async with http_client.stream(
                "POST",
                LOCAL_ENDPOINT,
                json=payload,
                headers={
                    "Content-Type": "application/json"
                }
            ) as response:
                if response.status_code != 200:
                    yield f'data: {{"error": "Local server error: Status {response.status_code}"}}\n\n'
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
            yield f'data: {{"error": "Local streaming error: {str(e)}"}}\n\n'

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# Monta static files
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)