import streamlit as st
import requests

st.set_page_config(page_title="全格式智能摘要", page_icon="📑", layout="wide")

# 初始化
if "history" not in st.session_state:
    st.session_state.history = []
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

API_URL = "http://localhost:8000"

# ================== 左侧边栏 ==================
with st.sidebar:
    st.title("📂 文件上传")
    uploaded_file = st.file_uploader(
        "支持：PDF / Word / Excel / PPT / 视频 / 音频",
        type=["pdf", "docx", "xlsx", "pptx", "mp4", "m4a", "mp3", "wav"]
    )
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.success(f"✅ {uploaded_file.name}")

    st.divider()
    st.title("📜 历史记录")
    if st.button("🧹 清空历史"):
        st.session_state.history = []
        st.rerun()

    for idx, item in enumerate(reversed(st.session_state.history)):
        with st.expander(f"记录 {len(st.session_state.history)-idx}"):
            st.write(f"文件：{item['filename']}")
            st.write(f"类型：{item['type']}")
            if 'question' in item:
                st.write(f"问题：{item['question']}")
            st.write(f"内容：{item['content'][:100]}...")

# ================== 主界面 ==================
st.title("📑 全格式文档智能摘要与问答")
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 智能摘要")
    if st.button("📝 生成摘要"):
        if not st.session_state.uploaded_file:
            st.warning("请先上传文件！")
        else:
            with st.spinner("正在解析..."):
                f = st.session_state.uploaded_file
                files = {"file": (f.name, f.getvalue(), f.type)}
                res = requests.post(f"{API_URL}/summary", files=files)
                data = res.json()
                if data["status"] == "success":
                    st.success("✅ 摘要生成完成")
                    st.write(data["summary"])
                    st.session_state.history.append({
                        "filename": f.name,
                        "type": "摘要",
                        "content": data["summary"]
                    })
                else:
                    st.error(f"错误：{data['message']}")

with col2:
    st.subheader("💬 智能问答")
    question = st.text_input("请输入你的问题：")
    if st.button("🔎 获取答案"):
        if not st.session_state.uploaded_file:
            st.warning("请先上传文件！")
        elif not question:
            st.warning("请输入问题！")
        else:
            with st.spinner("正在思考..."):
                f = st.session_state.uploaded_file
                files = {"file": (f.name, f.getvalue(), f.type)}
                data = {"question": question}
                res = requests.post(f"{API_URL}/chat", files=files, data=data)
                ret = res.json()
                if ret["status"] == "success":
                    st.success("✅ 回答完成")
                    st.write(ret["answer"])
                    st.session_state.history.append({
                        "filename": f.name,
                        "type": "问答",
                        "question": question,
                        "content": ret["answer"]
                    })
                else:
                    st.error(f"错误：{ret['message']}")