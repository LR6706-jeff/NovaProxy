import json
import os
from pydantic import BaseModel
from typing import List, Dict, Optional

class Config(BaseModel):
    nvidia_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_keys: List[str] = []
    model_mapping: Dict[str, str] = {
        "claude-3-5-sonnet-latest": "z-ai/glm-4-9b-chat",
        "claude-3-5-sonnet-20241022": "z-ai/glm-4-9b-chat",
        "claude-3-5-sonnet-20240620": "z-ai/glm-4-9b-chat",
        "claude-3-opus-latest": "z-ai/glm-4-9b-chat",
        "claude-3-opus-20240229": "z-ai/glm-4-9b-chat",
        "claude-3-5-haiku-latest": "z-ai/glm-4-9b-chat",
        "claude-3-5-haiku-20241022": "z-ai/glm-4-9b-chat",
        "claude-3-haiku-20240307": "z-ai/glm-4-9b-chat"
    }
    default_model: str = "z-ai/glm-4-9b-chat"
    server_api_key: Optional[str] = None
    port: int = 3001

CONFIG_FILE = "config.json"

def load_config() -> Config:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Config(**data)
        except Exception as e:
            print(f"Error loading config: {e}")
    return Config()

def save_config(config: Config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, indent=2, ensure_ascii=False)

CONFIG = load_config()
