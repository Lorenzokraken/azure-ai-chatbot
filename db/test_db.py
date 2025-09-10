"""
Test script for the database functionality.
This script demonstrates how to use the database for managing projects and chats.
"""

from db import DatabaseManager, get_db

def test_database():
    # Initialize database
    db = get_db()
    
    print("=== Database Test ===")
    
    # Create a project
    print("\n1. Creating a project...")
    project_id = db.create_project("Test Project", "A test project for chatbot")
    if project_id:
        print(f"Created project with ID: {project_id}")
    else:
        print("Failed to create project")
        return
    
    # Get all projects
    print("\n2. Getting all projects...")
    projects = db.get_all_projects()
    for project in projects:
        print(f"Project: {project['name']} (ID: {project['id']})")
    
    # Create a chat in the project
    print("\n3. Creating a chat...")
    sample_messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you for asking!"}
    ]
    
    chat_id = db.create_chat(project_id, "Test Chat", sample_messages)
    if chat_id:
        print(f"Created chat with ID: {chat_id}")
    else:
        print("Failed to create chat")
        return
    
    # Get chats for the project
    print("\n4. Getting chats for project...")
    chats = db.get_chats_by_project(project_id)
    for chat in chats:
        print(f"Chat: {chat['title']} (ID: {chat['id']})")
        print(f"Messages: {chat['messages']}")
    
    # Update the chat
    print("\n5. Updating chat...")
    updated_messages = sample_messages + [
        {"role": "user", "content": "What can you help me with?"},
        {"role": "assistant", "content": "I can help with many things! What do you need?"}
    ]
    
    success = db.update_chat(chat_id, messages=updated_messages)
    if success:
        print("Chat updated successfully")
    else:
        print("Failed to update chat")
    
    # Get the updated chat
    print("\n6. Getting updated chat...")
    updated_chat = db.get_chat(chat_id)
    if updated_chat:
        print(f"Updated chat messages: {updated_chat['messages']}")
    
    # Update project
    print("\n7. Updating project...")
    success = db.update_project(project_id, description="An updated test project")
    if success:
        print("Project updated successfully")
    else:
        print("Failed to update project")
    
    # Get updated project
    print("\n8. Getting updated project...")
    updated_project = db.get_project(project_id)
    if updated_project:
        print(f"Updated project description: {updated_project['description']}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_database()