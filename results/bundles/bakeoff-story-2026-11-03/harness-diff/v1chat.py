"""Talk to an OpenAI-compatible /v1 chat endpoint (llama.cpp's llama-server, vLLM) and
return Ollama /api/chat shapes, so the bake-off scripts run unchanged against either.

A host whose path ends in /v1 selects this path: `http://gpu-host:11434/v1`. Messages
stay in the Ollama shape inside the scripts (assistant tool_calls carry a dict of
arguments, tool results carry `tool_name`); the conversion to ids and JSON-string
arguments happens here, both ways.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


class MalformedToolCall(Exception):
    """The model produced a tool call whose arguments were not valid JSON."""


def is_v1(host: str) -> bool:
    return host.rstrip("/").endswith("/v1")


def _get(host: str, path: str, timeout: float = 15.0):
    try:
        with urllib.request.urlopen(host.rstrip("/") + path, timeout=timeout) as resp:
            return json.load(resp)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)[:200]}


def to_openai(messages: list) -> list:
    """Ollama-shaped history to OpenAI-shaped: ids on every tool call, tool results
    matched to those ids in order, arguments as JSON strings."""
    out, pending, n = [], [], 0
    for m in messages:
        role = m.get("role")
        if role == "assistant" and m.get("tool_calls"):
            calls, pending = [], []
            for c in m["tool_calls"]:
                fn = c.get("function") or c
                n += 1
                cid = c.get("id") or f"call_{n}"
                args = fn.get("arguments")
                if not isinstance(args, str):
                    args = json.dumps(args if args is not None else {})
                calls.append({"id": cid, "type": "function",
                              "function": {"name": fn.get("name"), "arguments": args}})
                pending.append(cid)
            out.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": calls})
        elif role == "tool":
            cid = m.get("tool_call_id") or (pending.pop(0) if pending else "call_0")
            msg = {"role": "tool", "tool_call_id": cid, "content": m.get("content") or ""}
            if m.get("tool_name"):
                msg["name"] = m["tool_name"]
            out.append(msg)
        else:
            out.append({"role": role, "content": m.get("content") or ""})
    return out


def from_openai(data: dict, wall: float) -> dict:
    """One /v1/chat/completions reply to the /api/chat shape the scripts read."""
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    calls = []
    for c in msg.get("tool_calls") or []:
        fn = c.get("function") or {}
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args) if args.strip() else {}
            except json.JSONDecodeError as exc:
                raise MalformedToolCall(f"invalid tool call arguments for {fn.get('name')}: {args[:200]}") from exc
        calls.append({"id": c.get("id"), "function": {"name": fn.get("name"), "arguments": args or {}}})
    finish = choice.get("finish_reason")
    usage = data.get("usage") or {}
    timings = data.get("timings") or {}
    message = {"role": "assistant", "content": msg.get("content") or ""}
    if msg.get("reasoning_content"):
        message["thinking"] = msg["reasoning_content"]
    if calls:
        message["tool_calls"] = calls
    predicted_ms = timings.get("predicted_ms")
    return {
        "model": data.get("model"),
        "message": message,
        "done": True,
        "done_reason": "length" if finish == "length" else "stop",
        "finish_reason": finish,
        "prompt_eval_count": usage.get("prompt_tokens", timings.get("prompt_n")),
        "eval_count": usage.get("completion_tokens", timings.get("predicted_n")),
        "eval_duration": int(predicted_ms * 1e6) if predicted_ms else None,
        "prompt_eval_duration": int(timings["prompt_ms"] * 1e6) if timings.get("prompt_ms") else None,
        "_timings": timings,
        "_wall": wall,
    }


def chat(host: str, model: str, messages: list, num_predict: int, tools=None, think: bool = False,
         seed: int = 0, timeout: float = 400.0, num_ctx: int | None = None) -> dict:
    """The protocol the bake-off uses, on /v1: temperature 0, a seed, a generation cap,
    thinking off through the chat template. num_ctx is the server's to set; it is
    accepted so call sites stay uniform and ignored."""
    payload = {
        "model": model,
        "messages": to_openai(messages),
        "stream": False,
        "temperature": 0,
        "seed": seed,
        "max_tokens": num_predict,
        "chat_template_kwargs": {"enable_thinking": bool(think)},
    }
    if tools is not None:
        payload["tools"] = tools
    req = urllib.request.Request(
        host.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return from_openai(data, time.perf_counter() - t0)


def seat(host: str, model: str) -> dict:
    """What defines the seat on a llama-server: build, model file, context, slots.
    GPU residency is not reported by the server; record it from the host."""
    root = host.rstrip("/")
    root = root[:-3] if root.endswith("/v1") else root  # /props is served beside /v1, not under it
    props = _get(root, "/props")
    models = _get(host, "/models")
    meta, details = {}, None
    for m in models.get("data") or []:
        if m.get("id") == model:
            meta = m.get("meta") or {}
            details = {"format": "gguf", "ftype": meta.get("ftype"), "n_params": meta.get("n_params"),
                       "n_ctx_train": meta.get("n_ctx_train"), "owned_by": m.get("owned_by")}
    path = props.get("model_path") or ""
    return {
        "host": host, "model": model, "api": "openai-v1",
        "server": props.get("build_info"),
        "digest": path.rsplit("sha256-", 1)[-1] if "sha256-" in path else None,
        "model_path": path, "size": meta.get("size"), "details": details,
        "loaded": {"context_length": props.get("n_ctx") or (props.get("default_generation_settings") or {}).get("n_ctx"),
                   "total_slots": props.get("total_slots"), "runner": "llamacpp",
                   "gpu_percent": None, "size": meta.get("size"), "size_vram": None},
        "served": [m.get("id") for m in models.get("data") or []],
    }
