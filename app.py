"""K_ai_D 聊天机器人 —— Streamlit + 本地 Ollama（走 OpenAI 兼容接口）。

启动（必须用 streamlit run；直接 python app.py 只会得到一片空白）：
    .\\.venv\\Scripts\\Activate.ps1
    streamlit run app.py

前提：本机 Ollama 已启动（127.0.0.1:11434），且已拉取 qwen2.5:7b 模型。
"""

import streamlit as st
from openai import OpenAI

# 指向本机 Ollama 的 OpenAI 兼容接口。
# 好处：以后想换成 DeepSeek、通义等云端模型，只需改 base_url 和 api_key，
# 下面的调用代码一行都不用动。本地服务不校验 key，填个占位值即可。
client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")


def im():
    """返回一份全新的初始对话：人设 + 开场问候。

    每次调用都新建一个列表，所以“首次进入页面”和“点清空对话”拿到的是
    互不影响的两份数据。若改成模块级常量直接赋值，两处会共用同一个列表对象，
    之后往 messages 里 append 会把这份“模板”也改掉。
    """
    return [
        # system 是“人设”，必须排第一条。它只发给模型看，不在界面上显示。
        {"role": "system", "content": "你是一个聊天机器人"},
        # 开场问候也放进历史里，模型才知道自己说过这句话；
        # 它会由下面的历史循环渲染出来，所以界面代码里不需要再单独画一次。
        {"role": "assistant", "content": "您好，我是K_ai_D聊天机器人，有什么可以帮助您的吗！"},
    ]


# Streamlit 每接收一次交互（输入、点按钮）就把整个脚本从头重跑一遍。
# 普通变量每次重跑都会被重置，只有 session_state 里的数据能跨重跑存活。
# 注意：它只活在“当前浏览器会话”里，F5 刷新或关掉标签页就会清空。
if "messages" not in st.session_state:
    st.session_state.messages = im()

st.title("K_ai_D聊天机器人")
st.caption("本地部署 · 数据不出本机")
st.divider()

with st.sidebar:
    st.caption("模型: qwen2.5:7b")

    # st.button() 返回 True/False，只有被点击的那一次返回 True，所以要用 if 判断
    if st.button("清空对话"):
        # 重置成一份新的初始对话（含开场问候），再强制重跑一次让界面立刻刷新。
        # 这里必须重新调用 im()，否则问候语会在清空后消失。
        st.session_state.messages = im()
        st.rerun()

# 渲染历史消息。
# [1:] 跳过索引 0 的 system —— 它只给模型看，不该出现在聊天界面上。
# 索引 1 的开场问候也会在这里被画出来。
for m in st.session_state.messages[1:]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

text = st.chat_input("说点什么")
if text:
    # 1) 用户消息先入库。上面那个历史循环本轮已经跑过了，
    #    所以紧接着要当场补画一次，否则这句会“慢一拍”才出现。
    st.session_state.messages.append({"role": "user", "content": text})

    with st.chat_message("user"):
        st.markdown(text)

    # 2) 调用模型。传的是整个历史 —— 模型本身没有记忆，
    #    它能“记得上文”的唯一原因，就是每次都把全量对话重新发一遍。
    with st.spinner("思考中..."):
        try:
            resp = client.chat.completions.create(
                model="qwen2.5:7b",
                messages=st.session_state.messages,
            )
            # 返回是 OpenAI 格式：choices[0] 是第一个候选答案
            回答 = resp.choices[0].message.content
        except Exception as e:
            # 失败时把刚入库的用户消息撤回，避免界面留下“半条对话”；
            # 再终止本次运行，否则下面会用到未定义的 回答 变量。
            st.session_state.messages.pop()
            st.error(f"模型调用失败：{e}")
            st.stop()

    # 3) 模型的回答同样要入库，否则它不记得自己说过什么，聊几轮就开始重复。
    st.session_state.messages.append({"role": "assistant", "content": 回答})

    with st.chat_message("assistant"):
        st.markdown(回答)