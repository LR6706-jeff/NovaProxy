import json
import uuid
from typing import List, Dict, Any, Optional

def convert_anthropic_to_openai(anthropic_req: Dict[str, Any], model_mapping: Dict[str, str], default_model: str) -> Dict[str, Any]:
    orig_model = anthropic_req.get("model", "")
    target_model = model_mapping.get(orig_model, orig_model if orig_model else default_model)
    
    system_content = ""
    system_raw = anthropic_req.get("system")
    if isinstance(system_raw, str):
        system_content = system_raw
    elif isinstance(system_raw, list):
        system_content = "\n".join([b.get("text", "") for b in system_raw if b.get("type") == "text"])

    messages = []
    if system_content:
        messages.append({"role": "system", "content": system_content})

    for msg in anthropic_req.get("messages", []):
        role = msg.get("role")
        content = msg.get("content")
        
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            parts = []
            for block in content:
                if not block:
                    continue
                b_type = block.get("type")
                if b_type == "text":
                    parts.append({"type": "text", "text": block.get("text", "")})
                elif b_type == "image":
                    source = block.get("source", {})
                    if source.get("type") == "base64":
                        parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{source.get('media_type')};base64,{source.get('data')}"}
                        })
                elif b_type == "tool_use":
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": json.dumps(block.get("input", {}))
                            }
                        }]
                    })
                elif b_type == "tool_result":
                    messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": str(block.get("content", ""))
                    })
            if parts:
                messages.append({"role": role, "content": parts})

    openai_tools = []
    for t in anthropic_req.get("tools", []):
        if not t:
            continue
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t.get("name"),
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {})
            }
        })

    openai_req = {
        "model": target_model,
        "messages": messages,
        "max_tokens": anthropic_req.get("max_tokens", 4096),
        "temperature": anthropic_req.get("temperature", 0.7),
        "stream": anthropic_req.get("stream", False)
    }
    if openai_tools:
        openai_req["tools"] = openai_tools
    
    return openai_req

class StreamTranslator:
    def __init__(self, model: str):
        self.model = model
        self.current_block_type = None
        self.current_tool_id = None

    def translate_chunk(self, chunk_json: Dict[str, Any]) -> List[str]:
        """将 OpenAI 格式的流式 chunk 转换为 Anthropic SSE 事件"""
        events = []
        
        # 防御性检查：确保 chunk_json 是 dict
        if not chunk_json or not isinstance(chunk_json, dict):
            return events
        
        choices = chunk_json.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            return events
        
        first_choice = choices[0]
        if not first_choice or not isinstance(first_choice, dict):
            return events
        
        delta = first_choice.get("delta")
        if delta is None:
            delta = {}
        
        finish_reason = first_choice.get("finish_reason")

        # 1. 处理文本内容
        content = delta.get("content") if isinstance(delta, dict) else None
        if content is not None and content != "":
            if self.current_block_type != "text":
                if self.current_block_type == "tool_use":
                    events.append(self._make_event("content_block_stop", {"index": 0}))
                events.append(self._make_event("content_block_start", {
                    "index": 0, "content_block": {"type": "text", "text": ""}
                }))
                self.current_block_type = "text"
            
            events.append(self._make_event("content_block_delta", {
                "index": 0, "delta": {"type": "text_delta", "text": str(content)}
            }))

        # 2. 处理工具调用
        if isinstance(delta, dict):
            tool_calls = delta.get("tool_calls")
            if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
                tc = tool_calls[0]
                if tc and isinstance(tc, dict):
                    func = tc.get("function")
                    if func and isinstance(func, dict):
                        func_name = func.get("name")
                        if func_name:
                            if self.current_block_type == "text":
                                events.append(self._make_event("content_block_stop", {"index": 0}))
                            
                            self.current_block_type = "tool_use"
                            self.current_tool_id = tc.get("id") or f"toolu_{uuid.uuid4().hex[:12]}"
                            events.append(self._make_event("content_block_start", {
                                "index": 0,
                                "content_block": {
                                    "type": "tool_use",
                                    "id": self.current_tool_id,
                                    "name": func_name,
                                    "input": {}
                                }
                            }))
                        
                        func_args = func.get("arguments")
                        if func_args:
                            events.append(self._make_event("content_block_delta", {
                                "index": 0,
                                "delta": {"type": "input_json_delta", "partial_json": str(func_args)}
                            }))

        # 3. 处理结束
        if finish_reason:
            if self.current_block_type:
                events.append(self._make_event("content_block_stop", {"index": 0}))
            
            reason_map = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use"}
            usage = chunk_json.get("usage") or {}
            events.append(self._make_event("message_delta", {
                "delta": {"stop_reason": reason_map.get(finish_reason, "end_turn"), "stop_sequence": None},
                "usage": {"output_tokens": usage.get("completion_tokens", 0) if isinstance(usage, dict) else 0}
            }))
            events.append(self._make_event("message_stop", {}))

        return events

    def _make_event(self, event_type: str, data: Dict[str, Any]) -> str:
        data["type"] = event_type
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
