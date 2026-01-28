import json
import asyncio
import httpx
import itertools
import time
import socket
import webbrowser
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from config_load import CONFIG, Config, save_config
from translator import convert_anthropic_to_openai, StreamTranslator

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 全局 HTTP 客户端 - 连接复用，大幅提升稳定性和速度
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # 启动时创建客户端，配置连接池和超时
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(300.0, connect=30.0),  # 总超时5分钟，连接超时30秒
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
    )
    print(f"✨ NovaProxy 已启动: http://localhost:{CONFIG.port}")
    yield
    await http_client.aclose()

app = FastAPI(title="NovaProxy", lifespan=lifespan)

# Stats & Logging
class Stats:
    request_count = 0
    token_count = 0
    logs = []

stats = Stats()

def add_log(method: str, path: str, status: str):
    now = datetime.now().strftime("%H:%M:%S")
    stats.logs.append({"time": now, "method": method, "path": path, "status": status})
    if len(stats.logs) > 50:
        stats.logs.pop(0)

templates = Jinja2Templates(directory=get_resource_path("templates"))

# Key cycler
key_cycle = None
def init_key_cycle():
    global key_cycle
    key_cycle = itertools.cycle(CONFIG.nvidia_keys) if CONFIG.nvidia_keys else None
init_key_cycle()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    current_logs = stats.logs[:]
    stats.logs = []
    return {
        "requests": stats.request_count,
        "tokens": stats.token_count,
        "ip": local_ip,
        "logs": current_logs
    }

@app.get("/api/config")
async def get_current_config():
    return CONFIG.dict()

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    CONFIG.nvidia_keys = new_config.get("nvidia_keys", CONFIG.nvidia_keys)
    CONFIG.model_mapping = new_config.get("model_mapping", CONFIG.model_mapping)
    CONFIG.server_api_key = new_config.get("server_api_key")
    save_config(CONFIG)
    init_key_cycle()
    return {"status": "ok"}

async def call_nvidia_with_retry(openai_req: dict, api_key: str, max_retries: int = 3):
    """带重试的 NVIDIA API 调用"""
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = await http_client.post(
                CONFIG.nvidia_url,
                json=openai_req,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            resp.raise_for_status()
            return resp
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            last_error = e
            add_log("POST", f"Retry {attempt+1}/{max_retries}", str(e)[:50])
            await asyncio.sleep(1 * (attempt + 1))  # 递增等待
        except httpx.HTTPStatusError as e:
            # 非重试类错误直接抛出
            raise e
    raise last_error

@app.post("/v1/messages")
async def proxy_messages(request: Request):
    stats.request_count += 1
    try:
        anthropic_req = await request.json()
    except Exception:
        add_log("POST", "/v1/messages", "Invalid JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    auth_header = request.headers.get("x-api-key") or request.headers.get("authorization", "")
    if CONFIG.server_api_key and CONFIG.server_api_key not in auth_header:
        add_log("POST", "/v1/messages", "401 Unauthorized")
        raise HTTPException(status_code=401, detail="Invalid API Key")

    openai_req = convert_anthropic_to_openai(anthropic_req, CONFIG.model_mapping, CONFIG.default_model)
    is_stream = openai_req.get("stream", False)

    if not key_cycle:
        add_log("POST", "/v1/messages", "500 No API Keys")
        raise HTTPException(status_code=500, detail="No NVIDIA API keys configured")
    api_key = next(key_cycle)

    add_log("POST", f"/v1/messages -> {openai_req['model']}", "Processing")
    
    if not is_stream:
        try:
            resp = await call_nvidia_with_retry(openai_req, api_key)
            data = resp.json()
            text = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})
            stats.token_count += usage.get("total_tokens", 0)
            
            return {
                "id": f"msg_{uuid.uuid4().hex[:12]}",
                "type": "message",
                "role": "assistant",
                "model": openai_req["model"],
                "content": [{"type": "text", "text": text}],
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0)
                }
            }
        except Exception as e:
            add_log("POST", "/v1/messages", f"Error: {str(e)[:50]}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # 流式响应
        async def stream_generator():
            msg_id = f"msg_{uuid.uuid4().hex[:12]}"
            translator = StreamTranslator(openai_req["model"])
            
            # 必须先发送 message_start 事件
            yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': openai_req['model'], 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
            
            try:
                async with http_client.stream(
                    "POST", CONFIG.nvidia_url,
                    json=openai_req,
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=300.0
                ) as response:
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            events = translator.translate_chunk(chunk)
                            for e in events:
                                yield e
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                add_log("STREAM", "/v1/messages", f"Error: {str(e)[:50]}")
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'message': str(e)}})}\n\n"
        
        return StreamingResponse(
            stream_generator(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
            }
        )

def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{CONFIG.port}")

if __name__ == "__main__":
    import uvicorn
    import threading

    # 修复在某些 Windows 环境下 sys.stdout 为 None 导致 uvicorn 崩溃的问题
    if sys.stdout is None:
        class DummyStream:
            def write(self, data): pass
            def flush(self): pass
            def isatty(self): return False
        sys.stdout = DummyStream()
    if sys.stderr is None:
        sys.stderr = sys.stdout

    try:
        threading.Thread(target=open_browser, daemon=True).start()
        # 禁用颜色输出，彻底避免 isatty 检查导致的崩溃
        uvicorn.run(app, host="0.0.0.0", port=CONFIG.port, log_level="warning", use_colors=False)
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            print(f"\n❌ 错误：端口 {CONFIG.port} 已被占用！")
            print("请先关闭其他正在运行的 NovaProxy 实例，或使用端口清理工具。")
        else:
            print(f"\n❌ 启动失败：{e}")
        input("\n按回车键退出...")
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        input("\n按回车键退出...")

