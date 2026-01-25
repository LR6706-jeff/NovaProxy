import json
import uuid
import time
from typing import List, Dict, Any, Optional

def convert_anthropic_to_openai(anthropic_req: Dict[str, Any], model_mapping: Dict[str, str], default_model: str) -> Dict[str, Any]:
    # 1. Model Mapping
    orig_model = anthropic_req.get("model", "")
    target_model = model_mapping.get(orig_model, orig_model if orig_model else default_model)
    
    # 2. Extract System Prompt
    system_content = ""
    system_raw = anthropic_req.get("system")
    if isinstance(system_raw, str):
        system_content = system_raw
    elif isinstance(system_raw, list):
        system_content = "\n".join([b.get("text", "") for b in system_raw if b.get("type") == "text"])

    messages = []
    if system_content:
        messages.append({"role": "system", "content": system_content})

    # 3. Process Messages
    for msg in anthropic_req.get("messages", []):
        role = msg.get("role")
        content = msg.get("content")
        
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            parts = []
            for block in content:
                b_type = block.get("type")
                if b_type == "text":
                    parts.append({"type": "text", "text": block.get("text")})
                elif b_type == "image":
                    source = block.get("source", {})
                    if source.get("type") == "base64":
                        parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{source.get('media_type')};base64,{source.get('data')}"
                            }
                        })
                elif b_type == "tool_result":
                    # Tool results in Anthropic are part of messages, in OpenAI they are separate 'tool' role messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": str(block.get("content", ""))
                    })
            if parts:
                messages.append({"role": role, "content": parts})

    # 4. Tools
    openai_tools = []
    for t in anthropic_req.get("tools", []):
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
        "max_tokens": anthropic_req.get("max_tokens", 1024),
        "temperature": anthropic_req.get("temperature", 0.7),
        "stream": anthropic_req.get("stream", False)
    }
    if openai_tools:
        openai_req["tools"] = openai_tools
    
    return openai_req

def openai_to_anthropic_stream(chunk_json: Dict[str, Any], model: str) -> Optional[str]:
    """Converts an OpenAI stream chunk to Anthropic SSE format."""
    choices = chunk_json.get("choices", [])
    if not choices:
        return None
    
    delta = choices[0].get("delta", {})
    finish_reason = choices[0].get("finish_reason")
    
    # Text content
    if "content" in delta and delta["content"]:
        return json.dumps({
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": delta["content"]}
        })
    
    # Tool calls (simplified)
    if "tool_calls" in delta:
        tc = delta["tool_calls"][0]
        # This is complex in streaming, providing a simplified version
        # Correct implementation would track tool call indices
        return json.dumps({
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": tc.get("function", {}).get("arguments", "")}
        })

    if finish_reason:
        reason_map = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use"}
        return json.dumps({
            "type": "message_delta",
            "delta": {"stop_reason": reason_map.get(finish_reason, "end_turn"), "stop_sequence": None},
            "usage": {"output_tokens": 0}
        })
    
    return None
