import os
from dotenv import load_dotenv

# Current: backend/main.py
# Goal: YT/.env

# 1. backend
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Current dir: {current_dir}")

# 2. webinar_app
parent_dir = os.path.dirname(current_dir)
print(f"Parent dir: {parent_dir}")

# 3. YT
grandparent_dir = os.path.dirname(parent_dir)
print(f"Grandparent dir: {grandparent_dir}")

env_path = os.path.join(grandparent_dir, '.env')
print(f"Looking for .env at: {env_path}")

if os.path.exists(env_path):
    print("✅ .env file found!")
    load_dotenv(env_path)
    project_id = os.getenv("RAG_PROJECT_ID")
    if project_id:
        print(f"✅ RAG_PROJECT_ID loaded: {project_id}...")
    else:
        print("❌ RAG_PROJECT_ID not found in .env")
else:
    print("❌ .env file NOT found")
