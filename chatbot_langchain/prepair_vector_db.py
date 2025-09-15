import os
import json
import requests
import sqlite3
from datetime import datetime
import re

class RAGHandler:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, 'chatbot_langchain', 'docs')
        self.api_key = "123"  # Token cho Together AI
        self.model = "meta-llama/Llama-2-70b-chat-hf"  # Model mặc định
        self.api_url = "https://api.together.xyz/v1/completions"
        
    // ... existing code ...