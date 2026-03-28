"""JSON 提取工具 — 兼容 LLM 返回 markdown 代码块或非 JSON 包装"""
from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict:
    """
    从 LLM 响应文本中提取 JSON 对象。
    支持:
    1. 纯 JSON: {"key": "value"}
    2. Markdown 代码块: ```json\n{...}\n```
    3. 嵌入文本中: 这里是结果 {"key": "value"} 结束
    """
    text = text.strip()

    # 提取 ```json ... ``` 代码块
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    # 如果最外层不是 { 或 [，找到第一个完整 JSON 对象
    if not text.startswith(("{", "[")):
        start = text.find("{")
        if start == -1:
            raise ValueError(f"No JSON object found in response: {text[:300]}")
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        text = text[start:end]

    return json.loads(text)
