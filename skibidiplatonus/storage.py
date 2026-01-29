import json
import os
from typing import Any

class SimpleJSONStorage:
    def __init__(self, path: str):
        self.path = path
        self.storage: dict[str, Any] = {}

        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.storage = {}
            return
        
        with open(self.path) as f:
            self.storage = json.load(f)
    
    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.storage, f)