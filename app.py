import streamlit as st
import requests

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

BASE_URL = "http://127.0.0.1:8000"

# 状态
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""
if "expanded_index" not in st.session_state:
    st.session_state.expanded_index = None
if "show_history" not in st.session_state:
    st.session_state.show_history = False

# ===================== 左侧边栏 =====================
with st.sidebar:
    st.title("📂 文件上传")
    # ✅ 这里已支持视频上传
    uploaded_file = st.file_uploader("上传文件", type=["pdf","docx","doc","xlsx","pptx","m4a","mp3","mp4","mov","avi","mkv","txt"])
    st.divider()

    if st.button("🔍 生成摘要", use_container_width=True, type="primary"):
        if uploaded_file:
            with st.spinner("生成中..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    res = requests.post(BASE_URL+"/summary", files=files, timeout=120)
                    if res.status_code == 200:
                        st.session_state.summary_text = res.json()["summary"]
                        st.success("✅ 摘要完成")
                except:
                    st.error("请求超时")

    st.divider()
    if st.button("📜 浏览历史", use_container_width=True):
        st.session_state.show_history = True
    if st.session_state.show_history:
        if st.button("📄 返回摘要", use_container_width=True):
            st.session_state.show_history = False

# ===================== 右侧 =====================
if not st.session_state.show_history:
    st.title("📌 文档摘要")
    with st.container(border=True, height=300):
        st.write(st.session_state.summary_text if st.session_state.summary_text else "请上传文件生成摘要")

    st.divider()
    st.subheader("💬 智能问答")
    user_q = st.text_input("输入问题（支持通用问题）：")
    if st.button("📤 发送", use_container_width=True):
        if user_q:
            with st.spinner("处理中..."):
                try:
                    if uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        res = requests.post(BASE_URL+"/chat", files=files, data={"question": user_q}, timeout=120)
                    else:
                        res = requests.post(BASE_URL+"/chat_without_file", json={"question": user_q}, timeout=120)

                    if res.status_code == 200:
                        ans = res.json()["answer"]
                        st.session_state.chat_history.append({"question":user_q, "answer":ans})
                        st.rerun()
                except:
                    st.success("✅ 发送成功，正在加载回答...")

    if st.session_state.chat_history:
        last = st.session_state.chat_history[-1]
        st.divider()
        st.markdown(f"**🙂 问题：** {last['question']}")
        st.markdown(f"**🤖 回答：** {last['answer']}")

else:
    st.title("📜 历史记录")
    for i, chat in enumerate(st.session_state.chat_history):
        with st.container(border=True):
            st.markdown(f"**Q{i+1}：** {chat['question']}")
            ans = chat["answer"]
            if st.session_state.expanded_index != i:
                st.write(ans[:150] + "...")
                if st.button("查看全部", key=f"s{i}"):
                    st.session_state.expanded_index = i
                    st.rerun()
            else:
                st.write(ans)
                if st.button("收起", key=f"h{i}"):
                    st.session_state.expanded_index = None
                    st.rerun()