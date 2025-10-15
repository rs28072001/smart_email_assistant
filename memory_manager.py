import json
from typing import List, Dict, Any
from config import Config

class MemoryManager:
    def __init__(self, memory_file: str = "memory.json"):
        self.memory_file = memory_file
        self.max_length = Config.MAX_HISTORY_LENGTH
    
    def load_memory(self, email_from: str) -> List[Dict[str, Any]]:
        """Load conversation history for a specific email address"""
        try:
            with open(self.memory_file, 'r') as f:
                all_memory = json.load(f)
                return all_memory.get(email_from, [])[-self.max_length:]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_memory(self, email_from: str, new_message: Dict[str, Any]):
        """Save new message to conversation history"""
        try:
            with open(self.memory_file, 'r') as f:
                all_memory = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_memory = {}
        
        if email_from not in all_memory:
            all_memory[email_from] = []
        
        all_memory[email_from].append(new_message)
        
        # Keep only the last N messages
        all_memory[email_from] = all_memory[email_from][-self.max_length:]
        
        with open(self.memory_file, 'w') as f:
            json.dump(all_memory, f, indent=2)
    
    def get_memory_context(self, email_from: str) -> str:
        """Get formatted memory context for LLM"""
        history = self.load_memory(email_from)
        if not history:
            return "No previous conversation history."
        
        context_parts = ["Previous conversation history:"]
        for i, msg in enumerate(history, 1):
            context_parts.append(f"{i}. From: {msg.get('from', 'Unknown')}")
            context_parts.append(f"   Subject: {msg.get('subject', 'No subject')}")
            context_parts.append(f"   Body: {msg.get('body', 'No content')}")
            context_parts.append("")
        
        return "\n".join(context_parts)