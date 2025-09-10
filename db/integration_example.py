"""
Integration example showing how to use the database in the main chatbot application.
This file demonstrates how to integrate the database functionality with the FastAPI backend.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from db import get_db

app = FastAPI()

# Pydantic models for request/response validation
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ChatCreate(BaseModel):
    project_id: int
    title: str
    messages: Optional[List[Dict[str, Any]]] = []

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None

# Initialize database
db = get_db()

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
    chat_id = db.create_chat(chat.project_id, chat.title, chat.messages)
    if not chat_id:
        raise HTTPException(status_code=400, detail="Failed to create chat. Project may not exist.")
    return {"id": chat_id, "project_id": chat.project_id, "title": chat.title}

@app.get("/api/projects/{project_id}/chats")
def get_chats(project_id: int):
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
        messages=chat.messages
    )
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat updated successfully"}

@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: int):
    """Delete a chat."""
    success = db.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

# Initialize database when the app starts
@app.on_event("startup")
def startup_event():
    """Initialize the database when the application starts."""
    db.init_database()
    print("Database initialized")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)