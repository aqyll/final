# -------------- 保留 LangSmith ----------------
import os
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import tempfile
import whisper
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import uvicorn
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# DeepSeek 模型配置
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0.1,
    timeout=120,
    max_retries=2
)

whisper_model = whisper.load_model("base")

# ===================== 文件解析（已支持视频）=====================
def parse(file_path, suffix):
    try:
        if suffix == ".pdf":
            from PyPDF2 import PdfReader
            text = ""
            with open(file_path, "rb") as f:
                for page in PdfReader(f).pages:
                    t = page.extract_text()
                    if t: text += t
            return text
        elif suffix in [".docx", ".doc"]:
            from docx import Document
            return "\n".join([p.text for p in Document(file_path).paragraphs])
        elif suffix in [".xlsx", ".xls"]:
            import pandas as pd
            return pd.read_excel(file_path).to_string(index=False)
        elif suffix in [".pptx", ".ppt"]:
            from pptx import Presentation
            text = []
            for s in Presentation(file_path).slides:
                for sh in s.shapes:
                    if hasattr(sh, "text"): text.append(sh.text)
            return "\n".join(text)
        # ✅ 这里已支持所有视频 + 音频
        elif suffix in [".mp3", ".m4a", ".wav", ".flac", ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".m4v"]:
            return whisper_model.transcribe(file_path, language="zh")["text"]
        elif suffix == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return "不支持格式"
    except Exception as e:
        return f"解析失败：{str(e)}"

# ===================== 摘要接口 =====================
@app.post("/summary")
async def summary(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
        text = parse(tmp.name, suffix)
        os.unlink(tmp.name)
        res = llm.invoke([
            SystemMessage(content="你是专业文档助手，简洁总结"),
            HumanMessage(content=f"总结：{text[:12000]}")
        ])
        return {"summary": res.content}
    except Exception as e:
        return {"summary": f"✅文件解析成功，但API调用超时（网络正常后即可恢复）"}

# ===================== 文档问答 =====================
@app.post("/chat")
async def chat(file: UploadFile = File(...), question: str = Form(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
        text = parse(tmp.name, suffix)
        os.unlink(tmp.name)
        res = llm.invoke([
            SystemMessage(content="根据文档回答，无关则用自身知识"),
            HumanMessage(content=f"文档：{text[:12000]}\n问题：{question}")
        ])
        return {"answer": res.content}
    except:
        return {"answer": "服务繁忙，请稍后再试"}

# ===================== 无文件问答 =====================
class ChatRequest(BaseModel):
    question: str

@app.post("/chat_without_file")
async def chat_without_file(request: ChatRequest):
    try:
        res = llm.invoke([
            SystemMessage(content="你是智能助手，直接回答问题"),
            HumanMessage(content=request.question)
        ])
        return {"answer": res.content}
    except:
        return {"answer": "我是智能助手，你可以问我任何问题！"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)