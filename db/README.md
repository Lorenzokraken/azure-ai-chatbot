# Database Structure

This directory contains the database implementation for managing projects and chats.

## Files

- `db.py`: Main database implementation using SQLite
- `test_db.py`: Test script to verify database functionality

## Database Schema

### Projects Table
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `name`: TEXT NOT NULL UNIQUE
- `description`: TEXT
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- `updated_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### Chats Table
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `project_id`: INTEGER NOT NULL (Foreign key to projects.id)
- `title`: TEXT NOT NULL
- `messages`: TEXT (JSON string containing the chat messages)
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- `updated_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Features

1. **Projects Management**:
   - Create, read, update, and delete projects
   - Each project can contain multiple chats

2. **Chats Management**:
   - Create chats within projects
   - Store chat messages as JSON
   - Update and delete chats

3. **Relationships**:
   - Chats are stored within projects (foreign key relationship)
   - Deleting a project automatically deletes all its chats (CASCADE DELETE)

## Usage

```python
from db import get_db

# Initialize database
db = get_db()

# Create a project
project_id = db.create_project("My Project", "A sample project")

# Create a chat within the project
chat_id = db.create_chat(project_id, "My Chat", [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"}
])

# Get all chats for a project
chats = db.get_chats_by_project(project_id)
```