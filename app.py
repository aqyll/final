import streamlit as st
import requests

st.set_page_config(page_title="智能文档工具", page_icon="📄", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

API_URL = "http://localhost:8000"

with st.sidebar:
    st.title("上传文件")
    file = st.file_uploader(
        "请上传文件",
        type=["pdf", "docx", "xlsx", "pptx", "mp4", "m4a", "mp3", "wav"]
    )

    st.divider()
    st.title("历史记录")
    if st.button("清空历史"):
        st.session_state.history = []

    for item in reversed(st.session_state.history):
        with st.expander(item["filename"]):
            st.write(f"类型：{item['type']}")
            st.write(item["content"][:80] + "...")

st.title("📑 全格式智能摘要与问答")

col1, col2 = st.columns(2)

with col1:
    st.subheader("智能摘要")
    if st.button("生成摘要"):
        if not file:
            st.warning("请先上传文件")
        else:
            with st.spinner("处理中..."):
                files = {"file": (file.name, file.getvalue(), file.type)}
                res = requests.post(f"{API_URL}/summary", files=files)
                data = res.json()
                if data["status"] == "success":
                    st.success("完成")
                    st.write(data["summary"])
                    st.session_state.history.append({
                        "filename": file.name,
                        "type": "摘要",
                        "content": data["summary"]
                    })
                else:
                    st.error("失败")

with col2:
    st.subheader("智能问答")
    q = st.text_input("输入问题")
    if st.button("提交问题"):
        if not file:
            st.warning("请先上传文件")
        elif not q:
            st.warning("请输入问题")
        else:
            with st.spinner("思考中..."):
                files = {"file": (file.name, file.getvalue(), file.type)}
                data = {"question": q}
                res = requests.post(f"{API_URL}/chat", files=files, data=data)
                ret = res.json()
                if ret["status"] == "success":
                    st.success("完成")
                    st.write(ret["answer"])
                    st.session_state.history.append({
                        "filename": file.name,
                        "type": "问答",
                        "content": ret["answer"]
                    })
                else:
                    st.error("失败")