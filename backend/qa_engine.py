# -*- coding: utf-8 -*-
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings

QA_SYSTEM = """You are a helpful code tutor explaining source code to learners. 
You have access to the source files of a project.
Answer questions in Chinese, with clear explanations even beginners can understand.
When referencing code, include the file path and line concepts.
Use analogies when helpful. Be encouraging and patient."""

def _build_qa_messages(project_context: str, conversation: list[dict], question: str) -> list:
    """Build message list for QA with conversation history."""
    msgs = [SystemMessage(content=QA_SYSTEM)]

    ctx = project_context[:40000] if len(project_context) > 40000 else project_context
    msgs.append(SystemMessage(content=f"Project source files:\n{ctx}"))

    for msg in conversation[-8:]:
        if msg["role"] == "user":
            msgs.append(HumanMessage(content=msg["content"]))
        else:
            msgs.append(SystemMessage(content=msg["content"], role="assistant"))

    msgs.append(HumanMessage(content=question))
    return msgs

async def answer_question(project_context: str, conversation: list[dict], question: str):
    """
    Stream answer tokens using LangChain's native async stream (astream_events).
    Each token is yielded as soon as the LLM produces it.
    """
    llm = ChatOpenAI(
        model=settings.deepseek_model,
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.5,
        max_tokens=4000,
        streaming=True,
        request_timeout=30,
    )

    messages = _build_qa_messages(project_context, conversation, question)

    try:
        # astream yields AIMessageChunk objects as they arrive
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        yield f"\n\n[错误: {str(e)}]"
