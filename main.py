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

# 加载配置
load_dotenv()
app = FastAPI(title="全格式智能问答系统")

# 模型配置
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1
)
parser = StrOutputParser()

# 语音模型
whisper_model = whisper.load_model("base")

# ------------------------------
# 全格式文档读取
# ------------------------------
def read_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t
        return text
    except:
        return "PDF文档解析失败"

def read_docx(path):
    try:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return "Word文档解析失败"

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
        return "PPT文档解析失败"

def read_xlsx(path):
    try:
        df = pd.read_excel(path, sheet_name=None)
        text = ""
        for name, sheet in df.items():
            text += f"【表格：{name}】\n"
            text += sheet.to_string(index=False) + "\n\n"
        return text
    except:
        return "Excel文档解析失败"

def read_audio_video(path):
    try:
        res = whisper_model.transcribe(path, language="zh", fp16=False)
        return res["text"].strip()
    except:
        return "音视频解析失败"

# 根据后缀选择解析器
def parse_file(path, suffix):
    if suffix == ".pdf": return read_pdf(path)
    elif suffix == ".docx": return read_docx(path)
    elif suffix == ".pptx": return read_pptx(path)
    elif suffix == ".xlsx": return read_xlsx(path)
    elif suffix in [".mp4", ".m4a", ".mp3", ".wav"]: return read_audio_video(path)
    else: return "不支持此格式"

# ------------------------------
# 摘要接口
# ------------------------------
@app.post("/summary")
async def summary(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            path = tmp.name

        content = parse_file(path, suffix)
        os.unlink(path)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是专业的文档总结助手，用简洁的中文总结核心内容。"),
            ("human", "文档内容：{text}")
        ])
        result = (prompt | llm | parser).invoke({"text": content})
        return {"status": "success", "summary": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ------------------------------
# ✅ 智能问答（修复版：支持表格/细节回答）
# ------------------------------
@app.post("/chat")
async def chat(file: UploadFile = File(...), question: str = Form(...)):
    try:
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            path = tmp.name

        # 读取完整内容
        content = parse_file(path, suffix)
        os.unlink(path)

        # ✅ 关键：强制模型必须从内容里找答案
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个严格基于文档内容回答的智能助手。
            1. 必须**只根据提供的内容**回答，不能编造信息。
            2. 如果内容里有表格，必须**仔细查看表格的每一行每一列**。
            3. 找到与问题匹配的信息后，**详细、准确、完整**地回答。
            4. 如果找不到答案，就说：“在文档中未找到相关信息”。
            """),
            ("human", "文档内容：{content}\n用户问题：{question}")
        ])

        answer = (prompt | llm | parser).invoke({
            "content": content,
            "question": question
        })

        return {"status": "success", "answer": answer}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)