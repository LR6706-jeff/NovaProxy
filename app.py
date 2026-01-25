import json
import asyncio
import httpx
import itertools
import os
import sys
import webbrowser
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from config_load import CONFIG, load_config
from translator import convert_anthropic_to_openai, openai_to_anthropic_stream

# 内部路径修复逻辑
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

app = FastAPI(title="NovaProxy")

try:
    templates_dir = get_resource_path("templates")
    templates = Jinja2Templates(directory=templates_dir)
except Exception as e:
    templates = None

key_iterator = itertools.cycle(CONFIG.nvidia_keys) if CONFIG.nvidia_keys else iter([])

def refresh_key_iterator():
    global key_iterator
    if CONFIG.nvidia_keys:
        key_iterator = itertools.cycle(CONFIG.nvidia_keys)
    else:
        key_iterator = iter([])

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    if not templates: return "Internal Error: Templates dir not found."
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status")
async def get_status():
    return {
        "keys": CONFIG.nvidia_keys,
        "key_count": len(CONFIG.nvidia_keys),
        "server_api_key": CONFIG.server_api_key,
        "model_map": CONFIG.model_mapping
    }

@app.post("/update_config")
async def update_config(new_config: dict):
    global CONFIG
    try:
        CONFIG.nvidia_keys = [k.strip() for k in new_config.get("nvidia_keys", []) if k.strip()]
        CONFIG.server_api_key = new_config.get("server_api_key", "")
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump({
                "nvidia_url": CONFIG.nvidia_url,
                "nvidia_keys": CONFIG.nvidia_keys,
                "model_mapping": CONFIG.model_mapping,
                "default_model": CONFIG.default_model,
                "server_api_key": CONFIG.server_api_key
            }, f, indent=2, ensure_ascii=False)
        
        refresh_key_iterator()
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/v1/messages")
async def handle_messages(request: Request):
    try: anthropic_req = await request.json()
    except: raise HTTPException(status_code=400, detail="Invalid JSON")

    if CONFIG.server_api_key:
        auth = request.headers.get("Authorization", "")
        key = request.headers.get("x-api-key", "")
        if not (auth == f"Bearer {CONFIG.server_api_key}" or key == CONFIG.server_api_key):
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    if not CONFIG.nvidia_keys:
        return JSONResponse(status_code=500, content={"error": "Key missing. Setup at http://localhost:3001"})

    openai_req = convert_anthropic_to_openai(anthropic_req, CONFIG.model_mapping, CONFIG.default_model)
    try: current_key = next(key_iterator)
    except StopIteration: return JSONResponse(status_code=500, content={"error": "No valid API keys"})
        
    headers = {"Authorization": f"Bearer {current_key}", "Content-Type": "application/json"}

    if not openai_req.get("stream"):
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(CONFIG.nvidia_url, json=openai_req, headers=headers)
            if resp.status_code != 200:
                try: return JSONResponse(status_code=resp.status_code, content=resp.json())
                except: return JSONResponse(status_code=resp.status_code, content={"error": "Upstream error"})
            
            oa_data = resp.json()
            choice = oa_data["choices"][0]
            msg = choice["message"]
            content = []
            if msg.get("content"): content.append({"type": "text", "text": msg["content"]})
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    content.append({
                        "type": "tool_use", "id": tc["id"], "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
                    })
            return {
                "id": oa_data["id"], "type": "message", "role": "assistant", "model": oa_data["model"],
                "content": content, "stop_reason": "end_turn",
                "usage": {"input_tokens": oa_data.get("usage", {}).get("prompt_tokens", 0), "output_tokens": oa_data.get("usage", {}).get("completion_tokens", 0)}
            }
    else:
        return StreamingResponse(stream_generator(openai_req, headers), media_type="text/event-stream")

async def stream_generator(openai_req, headers):
    import uuid
    msg_id = "msg_py_" + uuid.uuid4().hex
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': openai_req['model'], 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream("POST", CONFIG.nvidia_url, json=openai_req, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip() or line.strip() == "data: [DONE]": continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            converted = openai_to_anthropic_stream(chunk, openai_req["model"])
                            if converted:
                                data = json.loads(converted)
                                yield f"event: {data.get('type')}\ndata: {converted}\n\n"
                        except: continue
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    yield "event: message_stop\ndata: {\"type\": \"message_stop\"}\n\n"

def open_browser():
    """ 延迟一秒打开浏览器，确保后端已就绪 """
    import time
    time.sleep(1.5)
    webbrowser.open("http://localhost:3001")

if __name__ == "__main__":
    import uvicorn
    import threading
    # 开启线程自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=3001)
