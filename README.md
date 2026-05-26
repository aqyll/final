# 智能文档处理与问答系统
基于 Streamlit + FastAPI + DeepSeek + Whisper 开发的全格式文件解析、智能摘要、多轮问答工具。
支持 PDF / Word / Excel / PPT / 音频 / 视频等格式，可离线解析、联网生成智能回答。

## ✨ 功能特性
- 📄 **全格式文件解析**
  支持：pdf, docx, xlsx, pptx, txt, mp3, m4a, wav, mp4, mov, avi, mkv 等
- 🔍 **智能摘要生成**
  使用 DeepSeek 大模型自动生成结构化、简洁的内容摘要
- 💬 **智能文档问答**
  基于文件内容精准回答，支持跨文档知识问答
- 🌍 **通用问答能力**
  无需上传文件，直接进行 AI 对话
- 📜 **历史记录管理**
  查看历史问答，支持展开/收起完整回答
- 🎯 **界面清晰易用**
  左侧上传 + 右侧摘要 + 下方问答 + 历史页面切换

## 🏗 项目结构
final/├── backend/│ ├── main.py # FastAPI 后端服务│ └── .env # 密钥配置（DEEPSEEK_API_KEY、URL）├── frontend/│ └── app.py # Streamlit 前端界面├── requirements.txt # 依赖包└── README.md # 项目说明
plaintext

## 🚀 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```
2. 配置 .env 文件（backend 目录下）
```bash
DEEPSEEK_API_KEY=你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=你的LangSmith密钥
```
3. 启动后端
```bash
python backend/main.py
```
4. 启动前端
```bash
streamlit run frontend/app.py
```
📌 **使用说明**

左侧上传任意支持的文件

点击「生成摘要」获取文档总结

在下方输入框提问，支持：

基于文档内容的问题

与文档无关的通用问题

点击「浏览历史」查看所有问答记录

点击「返回摘要」回到主界面

🧩 **支持格式**

文档：pdf, docx, xlsx, pptx, txt

音频：mp3, m4a, wav, flac

视频：mp4, mov, avi, mkv, wmv

🛠 **技术栈**

前端：Streamlit

后端：FastAPI + Uvicorn

大模型：DeepSeek Chat

音视频转写：OpenAI Whisper

文档解析：PyPDF2 /python-docx/python-pptx /pandas

调试追踪：LangSmith

✅ **已解决问题**

支持 m4a /mp4 / 视频文件上传与解析

修复 LangSmith 连接报错

修复 Windows 10054 连接重置问题

修复前端 “后端连接失败” 提示

支持无文件通用问答

支持历史记录展开 / 收起

支持页面切换（摘要 ↔ 历史记录）