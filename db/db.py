import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

class DatabaseManager:
    def __init__(self, db_path: str = "chatbot.db"):
        """Initialize the database manager with the database path."""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This allows us to access columns by name
        return conn
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create chats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                context TEXT, -- RAG context for the chat
                messages TEXT,  -- JSON string containing the chat messages
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chats_project_id ON chats (project_id)
        ''')
        
        # RAG Tables - Essenziali per document storage e retrieval
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT, -- JSON array come stringa per semplicità
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES rag_documents (id) ON DELETE CASCADE
            )
        ''')
        
        # Indici per performance RAG
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rag_docs_project ON rag_documents (project_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_document ON rag_chunks (document_id)
        ''')
        
        conn.commit()
        conn.close()
    
    # Project methods
    def create_project(self, name: str, description: str = "") -> Optional[int]:
        """Create a new project and return its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO projects (name, description)
                VALUES (?, ?)
            ''', (name, description))
            
            project_id = cursor.lastrowid
            conn.commit()
            return project_id
        except sqlite3.IntegrityError:
            # Project with this name already exists
            conn.close()
            return None
        except Exception as e:
            conn.close()
            raise e
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM projects ORDER BY updated_at DESC')
        projects = cursor.fetchall()
        conn.close()
        
        return [dict(project) for project in projects]
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        project = cursor.fetchone()
        conn.close()
        
        return dict(project) if project else None
    
    def update_project(self, project_id: int, name: str = None, description: str = None) -> bool:
        """Update a project's information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build dynamic query based on provided fields
        fields = []
        values = []
        
        if name is not None:
            fields.append("name = ?")
            values.append(name)
        
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        
        if not fields:
            conn.close()
            return False
        
        # Add updated_at timestamp and project_id to values
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(project_id)
        
        query = f"UPDATE projects SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its chats."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # Chat methods
    def create_chat(self, project_id: Optional[int], title: str, messages: List[Dict[str, Any]] = None, context: str = "") -> Optional[int]:
        """Create a new chat within a project and return its ID."""
        # If project_id is provided, check if it exists
        if project_id is not None and not self.get_project(project_id):
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        messages_json = json.dumps(messages) if messages else json.dumps([])
        
        try:
            cursor.execute('''
                INSERT INTO chats (project_id, title, messages, context)
                VALUES (?, ?, ?, ?)
            ''', (project_id, title, messages_json, context))
            
            chat_id = cursor.lastrowid
            conn.commit()
            return chat_id
        except Exception as e:
            conn.close()
            raise e
    
    def get_chats_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all chats for a specific project."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chats 
            WHERE project_id = ? 
            ORDER BY updated_at DESC
        ''', (project_id,))
        
        chats = cursor.fetchall()
        conn.close()
        
        # Convert to dict and parse messages JSON
        result = []
        for chat in chats:
            chat_dict = dict(chat)
            try:
                chat_dict['messages'] = json.loads(chat_dict['messages'])
            except (json.JSONDecodeError, TypeError):
                chat_dict['messages'] = []
            result.append(chat_dict)
        
        return result
    
    def get_chat(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific chat by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM chats WHERE id = ?', (chat_id,))
        chat = cursor.fetchone()
        conn.close()
        
        if chat:
            chat_dict = dict(chat)
            try:
                chat_dict['messages'] = json.loads(chat_dict['messages'])
            except (json.JSONDecodeError, TypeError):
                chat_dict['messages'] = []
            return chat_dict
        
        return None
    
    def update_chat(self, chat_id: int, title: str = None, messages: List[Dict[str, Any]] = None, context: str = None) -> bool:
        """Update a chat's information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build dynamic query based on provided fields
        fields = []
        values = []
        
        if title is not None:
            fields.append("title = ?")
            values.append(title)
        
        if messages is not None:
            fields.append("messages = ?")
            values.append(json.dumps(messages))

        if context is not None:
            fields.append("context = ?")
            values.append(context)
        
        if not fields:
            conn.close()
            return False
        
        # Add updated_at timestamp and chat_id to values
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(chat_id)
        
        query = f"UPDATE chats SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_chat(self, chat_id: int) -> bool:
        """Delete a chat."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

# Global database instance
db = DatabaseManager()

# Convenience functions for common operations
def init_db():
    """Initialize the database."""
    global db
    db = DatabaseManager()

def get_db():
    """Get the database instance."""
    global db
    if 'db' not in globals() or db is None:
        init_db()
    return db