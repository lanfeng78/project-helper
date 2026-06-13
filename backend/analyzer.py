# -*- coding: utf-8 -*-
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings

SYSTEM_PROMPT_DETAIL = """You are an expert software architect who explains code to beginners.
Your task: analyze codebase text and produce a comprehensive, easy-to-understand report in Chinese.
Use simple analogies. Assume the reader knows basic programming but nothing about this project.

Output must be valid JSON with these fields (all in Chinese):
{
  "project_name": "项目名称",
  "one_line": "一句话简介（像跟朋友介绍那样）",
  "overview": "项目概述（200字以内，说清楚这项目是干嘛的，解决什么问题）",
  "tech_stack": "技术栈（列出主要语言、框架、工具，带简短说明）",
  "directory_structure": "目录结构（用树形展示，每个目录一句话说明用途）",
  "core_modules": [{"name": "模块名", "path": "路径", "description": "通俗解释这个模块干什么的"}],
  "data_flow": "数据流（用大白话讲数据怎么在系统里流动，像讲故事一样）",
  "design_patterns": [{"name": "设计模式", "location": "在哪里", "why": "为什么要这样设计"}],
  "entry_point": "入口文件及启动方式",
  "reading_guide": "阅读建议（如果你是新手，建议按什么顺序看代码，为什么）",
  "key_concepts": ["关键概念1", "关键概念2"],
  "pros": ["优点1", "优点2"],
  "cons": ["缺点或改进建议1"]
}

IMPORTANT: Return ONLY the JSON object, no markdown fences, no other text."""


SYSTEM_PROMPT_SIMPLE = """You are an expert software architect who explains code to beginners.
Your task: produce a CONCISE quick-overview of the codebase in Chinese — focus on speed and clarity over depth.
Use simple analogies. Aim for a report that takes ~30 seconds to read.

Output must be valid JSON with EXACTLY these 7 fields (all in Chinese, keep each field short):
{
  "project_name": "项目名称",
  "one_line": "一句话简介",
  "overview": "项目概述（150字以内）",
  "tech_stack": "主要技术栈（一句话列出核心语言/框架）",
  "directory_structure": "目录结构（精简树形，仅顶层 + 关键二级目录，每行一句话）",
  "entry_point": "入口文件及启动方式（1-2 句）",
  "reading_guide": "新手阅读顺序建议（3-5 步）"
}

IMPORTANT: Return ONLY the JSON object, no markdown fences, no other text. Keep it brief."""


def _build_llm(mode: str = "detail") -> ChatOpenAI:
    """Build a fresh ChatOpenAI per analysis call so mode→model is honored.

    Falls back to settings.deepseek_model when the mode-specific field is empty.
    """
    if mode == "simple":
        model = settings.deepseek_model_simple or settings.deepseek_model
        max_tokens = 3000
    else:
        model = settings.deepseek_model_detail or settings.deepseek_model
        max_tokens = 8000
    return ChatOpenAI(
        model=model,
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.3,
        max_tokens=max_tokens,
    )


# Back-compat shim: legacy callers (if any) of create_llm()/get_llm() still work.
def create_llm() -> ChatOpenAI:
    return _build_llm("detail")


ANALYSIS_LLM = None


def get_llm() -> ChatOpenAI:
    global ANALYSIS_LLM
    if ANALYSIS_LLM is None:
        ANALYSIS_LLM = create_llm()
    return ANALYSIS_LLM


async def analyze_codebase(context_text: str, mode: str = "detail", progress_cb=None) -> dict:
    """Analyze codebase text and return structured report as dict.

    mode = "simple" → uses flash model + trimmed context + 7-field prompt (fast, brief).
    mode = "detail" (default) → uses pro model + full context + 13-field prompt (thorough).
    """
    if progress_cb:
        progress_cb(0.75, "AI analyzing code structure...")

    llm = _build_llm(mode)
    system_prompt = SYSTEM_PROMPT_SIMPLE if mode == "simple" else SYSTEM_PROMPT_DETAIL
    max_chars = 24000 if mode == "simple" else 60000
    if len(context_text) > max_chars:
        context_text = context_text[:max_chars] + "\n\n[Content truncated due to size]"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this codebase:\n\n{context_text}")
    ]

    if progress_cb:
        progress_cb(0.80, "Generating report...")

    for attempt in range(3):
        try:
            response = llm.invoke(messages)
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("\n```", 1)[0]
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt == 2:
                raise
            messages.append(HumanMessage(content="Please return ONLY valid JSON, no other text. Try again."))

    if progress_cb:
        progress_cb(1.0, "Analysis complete!")
    return {}

def build_markdown_report(report: dict) -> str:
    """Convert structured report dict to beautiful markdown."""
    md = f"""# 📖 {report.get('project_name', '项目分析报告')}

> {report.get('one_line', '')}

---

## 📌 项目概述

{report.get('overview', '')}

---

## 🛠 技术栈

{report.get('tech_stack', '')}

---

## 📁 目录结构

```
{report.get('directory_structure', '')}
```

---

## 🧩 核心模块

"""
    for m in report.get("core_modules", []):
        md += f"### {m.get('name', '')}\n"
        md += f"- **路径**: `{m.get('path', '')}`\n"
        md += f"- **说明**: {m.get('description', '')}\n\n"

    md += f"""---

## 🌊 数据流

{report.get('data_flow', '')}

---

## 🎨 设计模式

"""
    for p in report.get("design_patterns", []):
        md += f"- **{p.get('name', '')}** — {p.get('location', '')}：{p.get('why', '')}\n"

    md += f"""

---

## 🚪 入口 & 启动

{report.get('entry_point', '')}

---

## 📚 阅读建议

{report.get('reading_guide', '')}

---

## 💡 关键概念

"""
    for c in report.get("key_concepts", []):
        md += f"- {c}\n"

    md += f"""

---

## ✅ 优点

"""
    for p in report.get("pros", []):
        md += f"- {p}\n"

    if report.get("cons"):
        md += f"""

---

## ⚠️ 可改进点

"""
        for c in report.get("cons", []):
            md += f"- {c}\n"

    md += "\n\n---\n\n*报告由 Project Helper AI 自动生成*"
    return md
