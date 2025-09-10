"""
Database initialization script.
This script can be run to initialize the database schema.
"""

import os
import sys

# Add the parent directory to the path so we can import from db
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db import get_db

def initialize_database():
    """Initialize the database schema."""
    print("Initializing database...")
    
    # This will create the database and tables if they don't exist
    db = get_db()
    
    # Test that we can create a project
    try:
        project_id = db.create_project("Default Project", "Default project for chatbot")
        if project_id:
            print("Database initialized successfully!")
            print(f"Created default project with ID: {project_id}")
        else:
            # Project might already exist, let's check
            projects = db.get_all_projects()
            if projects:
                print("Database already initialized.")
                print(f"Found {len(projects)} existing projects.")
            else:
                print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    initialize_database()