"""
Chat history management module
"""
import json
import os
from typing import List, Dict, Optional
import pandas as pd
from Agentic_RAG.config.settings import HISTORY_FILE, MAX_HISTORY_TURNS

class ChatHistoryManager:
    """
    Chat history manager class
    """
    def __init__(self):
        """Initialize chat history manager"""
        self.history: List[Dict] = self.load_history()
    
    # 1. Load chat history from file
    def load_history(self) -> List[Dict]:
        """
        Returns:
            List[Dict]: Chat history records list
        """
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")
        return []
    
    # 2. Save chat history to file
    def save_history(self) -> None:
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")
    
    # 3. Add new message to history
    def add_message(self, role: str, content: str) -> None:
        """
        Args:
            role (str): Message role ('user' or 'assistant')
            content (str): Message content
        """
        self.history.append({"role": role, "content": content})
        self.save_history()
    
    # 4. Clear chat history
    def clear_history(self) -> None:
        self.history = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
    
    # 5. Get formatted chat history
    def get_formatted_history(self, max_turns: int = MAX_HISTORY_TURNS) -> str:
        """
        Args:
            max_turns (int): Maximum number of conversation turns to retain
            
        Returns:
            str: Formatted chat history
        """
        if not self.history:
            return ""
        
        recent_history = self.history[-max_turns*2:] if len(self.history) > max_turns*2 else self.history
        
        formatted_history = "Previous conversation history:\n"
        for msg in recent_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role}: {msg['content']}\n"
        
        return formatted_history
    
    # 6. Export chat history to CSV file
    def export_to_csv(self) -> Optional[bytes]:
        """
        Export chat history to CSV

        Returns:
            Optional[bytes]: CSV content; None if export fails
        """
        try:
            df = pd.DataFrame(self.history)
            return df.to_csv(index=False).encode('utf-8')
        except Exception as e:
            print(f"Error exporting chat history: {str(e)}")
            return None
    
    # 7. Get chat history statistics
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics for chat history

        Returns:
            Dict[str, int]: Dictionary containing total message count and user message count
        """
        total_messages = len(self.history)
        user_messages = sum(1 for msg in self.history if msg["role"] == "user")
        return {
            "total_messages": total_messages,
            "user_messages": user_messages
        }
