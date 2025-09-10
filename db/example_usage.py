"""
Example of how to integrate the database with the main chatbot application.
"""

from db import get_db

def example_usage():
    """
    Example showing how to use the database in the main application.
    """
    # Get database instance
    db = get_db()
    
    # Create a new project for a user
    project_id = db.create_project(
        name="Web Development Project", 
        description="Chat history for web development assistance"
    )
    
    if not project_id:
        # Project might already exist, let's get it
        projects = db.get_all_projects()
        for project in projects:
            if project["name"] == "Web Development Project":
                project_id = project["id"]
                break
    
    # Add a chat to the project
    chat_id = db.create_chat(
        project_id=project_id,
        title="CSS Help Session",
        messages=[
            {"role": "user", "content": "How do I center a div both horizontally and vertically?"},
            {"role": "assistant", "content": "You can use Flexbox:\n\n```css\n.container {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  height: 100vh;\n}\n```"},
            {"role": "user", "content": "Thanks! What about for older browsers?"},
            {"role": "assistant", "content": "For older browsers, you can use this approach:\n\n```css\n.container {\n  position: relative;\n  height: 100vh;\n}\n\n.centered-div {\n  position: absolute;\n  top: 50%;\n  left: 50%;\n  transform: translate(-50%, -50%);\n}\n```"}
        ]
    )
    
    # Later, retrieve the chat history
    if chat_id:
        chat = db.get_chat(chat_id)
        print(f"Chat title: {chat['title']}")
        print("Messages:")
        for message in chat['messages']:
            print(f"  {message['role']}: {message['content']}")
    
    # Add another chat to the same project
    db.create_chat(
        project_id=project_id,
        title="JavaScript Debugging",
        messages=[
            {"role": "user", "content": "Why is my JavaScript function not working?"},
            {"role": "assistant", "content": "Can you share your code? I'll help you debug it."}
        ]
    )
    
    # Get all chats for the project
    chats = db.get_chats_by_project(project_id)
    print(f"\nProject has {len(chats)} chats:")
    for chat in chats:
        print(f"  - {chat['title']} (ID: {chat['id']})")

if __name__ == "__main__":
    example_usage()