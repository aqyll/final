from fastapi import FastAPI, UploadFile, File, Form
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import tempfile
import os
from dotenv import load_dotenv
import whisper
import docx
import pptx
import pandas as pd
from PyPDF2 import PdfReader

load_dotenv()
app = FastAPI()

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1
)
parser = StrOutputParser()
whisper_model = whisper.load_model("base")

def read_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t
        return text
    except:
        return "读取失败"

def read_docx(path):
    try:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return "读取失败"

def read_pptx(path):
    try:
        prs = pptx.Presentation(path)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text
    except:
        return "读取失败"

def read_xlsx(path):
    try:
        df = pd.read_excel(path, sheet_name=None)
        text = ""
        for name, sheet in df.items():
            text += f"表：{name}\n"
            text += sheet.to_string() + "\n\n"
        return text
    except:
        return "读取失败"

def read_av(path):
    try:
        res = whisper_model.transcribe(path, language="zh", fp16=False)
        return res["text"].strip()
    except:
        return "读取失败"

def parse(path, suffix):
    if suffix == ".pdf": return read_pdf(path)
    elif suffix == ".docx": return read_docx(path)
    elif suffix == ".pptx": return read_pptx(path)
    elif suffix == ".xlsx": return read_xlsx(path)
    elif suffix in [".mp4", ".m4a", ".mp3", ".wav"]: return read_av(path)
    else: return "不支持"

@app.post("/summary")
async def summary(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
        content = parse(tmp.name, suffix)
        os.unlink(tmp.name)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "请简洁总结内容"),
            ("human", "{text}")
        ])
        res = (prompt | llm | parser).invoke({"text": content})
        return {"status": "success", "summary": res}
    except:
        return {"status": "error"}

@app.post("/chat")
async def chat(file: UploadFile = File(...), question: str = Form(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
        content = parse(tmp.name, suffix)
        os.unlink(tmp.name)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "只根据文档内容回答，不编造"),
            ("human", "内容：{content}\n问题：{question}")
        ])
        res = (prompt | llm | parser).invoke({"content": content, "question": question})
        return {"status": "success", "answer": res}
    except:
        return {"status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)