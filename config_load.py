import json
import os
from pydantic import BaseModel
from typing import List, Dict, Optional

class Config(BaseModel):
    # 默认公开配置，不含任何私有信息
    nvidia_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_keys: List[str] = []
    model_mapping: Dict[str, str] = {}
    default_model: str = "z-ai/glm-4-9b-chat"
    server_api_key: Optional[str] = ""

def load_config(path: str = "config.json") -> Config:
    # 如果文件不存在，直接返回一个空白的初始配置对象
    if not os.path.exists(path):
        return Config()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 使用 Pydantic 进行校验加载
            return Config(**data)
    except Exception as e:
        # 如果文件损坏或解析失败，也返回空白配置，确保程序不崩溃
        print(f"[*] 注意: 配置文件加载失败 ({e}), 将使用默认配置运行。")
        return Config()

# 初始化全局配置对象
CONFIG = load_config()
