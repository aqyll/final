from fastapi import FastAPI, UploadFile, File, Form
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import tempfile
import os
import whisper
import docx
import pandas as pd
from PyPDF2 import PdfReader
from pptx import Presentation
from dotenv import load_dotenv

# 加载环境变量（LangSmith 会自动读取，不需要手动 setup）
load_dotenv()

app = FastAPI(title="文档智能问答API", version="1.0")

# ===================== LLM 模型初始化 =====================
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.1,
)

# 总结模板
prompt_summary = ChatPromptTemplate.from_messages([
    ("system", "你是专业的文档总结助手，用简洁、清晰、结构化的语言总结文本核心内容，不添加无关信息"),
    ("human", "请总结以下内容：\n{text}")
])

# 问答模板
prompt_chat = ChatPromptTemplate.from_messages([
    ("system", "你只能根据提供的文档内容回答问题，严禁编造信息。没有答案就说：无法从文档中找到相关答案"),
    ("human", "文档内容：{content}\n用户问题：{question}")
])

parser = StrOutputParser()

# 调用链
chain_summary = prompt_summary | llm | parser
chain_chat = prompt_chat | llm | parser

# ===================== 音频模型 =====================
whisper_model = whisper.load_model("base")

# ===================== 文件解析工具函数 =====================
def read_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def read_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pptx(file_path):
    prs = Presentation(file_path)
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
    return "\n".join(text)

def read_xlsx(file_path):
    df = pd.read_excel(file_path)
    return df.to_string(index=False)

def read_av(file_path):
    result = whisper_model.transcribe(file_path)
    return result["text"]

def parse(file_path, suffix):
    if suffix == ".pdf":
        return read_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return read_docx(file_path)
    elif suffix in [".pptx", ".ppt"]:
        return read_pptx(file_path)
    elif suffix in [".xlsx", ".xls"]:
        return read_xlsx(file_path)
    elif suffix in [".mp3", ".mp4", ".wav", ".flac"]:
        return read_av(file_path)
    elif suffix == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "不支持的文件格式"

# ===================== API 接口 =====================
@app.post("/summary", summary="文件总结")
async def summary(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
        content = parse(tmp.name, suffix)
        os.unlink(tmp.name)

        result = chain_summary.invoke(
            {"text": content},
            config={"metadata": {
                "function": "summary",
                "filename": file.filename
            }}
        )
        return {"status": "success", "summary": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/chat", summary="文档问答")
async def chat(file: UploadFile = File(...), question: str = Form(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
        content = parse(tmp.name, suffix)
        os.unlink(tmp.name)

        result = chain_chat.invoke(
            {"content": content, "question": question},
            config={"metadata": {
                "function": "chat",
                "filename": file.filename,
                "question": question
            }}
        )
        return {"status": "success", "answer": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)