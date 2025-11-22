#!/usr/bin/env python
"""
Launcher script for the Agentic RAG application.
Run this file to start the Streamlit app.

Usage:
    python run_app.py

Or directly with streamlit:
    streamlit run run_app.py
"""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the app
from Agentic_RAG.app import App

if __name__ == "__main__":
    app = App()
    app.run()

