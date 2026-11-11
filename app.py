"""本地聊天机器人 —— Streamlit + Ollama（OpenAI 兼容接口）。

启动方式（必须用 streamlit run，直接 python app.py 页面会是空白的）：
    .\\.venv\\Scripts\\Activate.ps1
    streamlit run app.py

前提：本机 Ollama 已启动，且已拉取 qwen2.5:7b 模型。
"""

import streamlit as st
from openai import OpenAI

# 指向本机 Ollama 的 OpenAI 兼容接口。
# 用这套接口的好处：以后换成云端模型（DeepSeek、通义等）只需改 base_url。
# api_key 本地服务不校验，写个占位值即可。
client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")

# Streamlit 每接收一次交互（输入、点按钮）就把整个脚本从头重跑一遍。
# 普通变量会被重置，只有 session_state 里的数据能跨重跑存活。
# 注意：它只活在"当前会话"里，浏览器 F5 刷新或关掉标签页就会清空。
if "messages" not in st.session_state:
    st.session_state.messages = [
        # system 是"人设"，永远排第一条，不会显示给用户看
        {"role": "system", "content": "你是一个聊天机器人"}
    ]

st.title("K_ai_D聊天机器人")
st.caption("本地部署 · 数据不出本机")
st.divider()

st.chat_message("assistant").write("您好，我是K_ai_D聊天机器人，有什么可以帮助您的吗！")

with st.sidebar:
    st.caption("模型: qwen2.5:7b")

    # st.button() 返回 True/False，只有被点击的那一次返回 True，所以要用 if 判断
    if st.button("清空对话"):
        # 重置成只有 system 的初始状态，再强制重跑一次让界面立刻刷新
        st.session_state.messages = [
            {"role": "system", "content": "你是一个聊天机器人"}
        ]
        st.rerun()

# 把历史渲染成气泡。
# [1:] 跳过第一条 system —— 它只给模型看，不该出现在聊天界面上。
for m in st.session_state.messages[1:]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

text = st.chat_input("说点什么")
if text:
    # 1) 用户消息先入库，下一轮重跑时由上面的循环负责显示
    st.session_state.messages.append({"role": "user", "content": text})

    # 2) 当场再画一遍：上面的循环在本轮已经跑过了，不画就会"慢一拍"
    with st.chat_message("user"):
        st.markdown(text)

    # 3) 调用模型。messages 传的是整个历史 —— 这就是模型"记得上文"的唯一原因，
    #    模型本身没有记忆，每次都要把全量对话重新发给它。
    with st.spinner("思考中..."):
        try:
            resp = client.chat.completions.create(
                model="qwen2.5:7b",
                messages=st.session_state.messages,
            )
            # 返回值是 OpenAI 格式：choices[0] 是第一个候选答案
            回答 = resp.choices[0].message.content
        except Exception as e:
            # 失败时撤回刚入库的用户消息，避免留下"半条对话"；
            # 然后终止本次运行，防止拿未定义的 回答 继续往下执行
            st.session_state.messages.pop()
            st.error(f"模型调用失败：{e}")
            st.stop()

    # 4) 模型的回答也要入库，否则它永远不记得自己说过什么，聊几轮就开始重复
    st.session_state.messages.append({"role": "assistant", "content": 回答})
    with st.chat_message("assistant"):
        st.markdown(回答)
        