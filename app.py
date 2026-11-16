"""K_ai_D 聊天机器人 —— Streamlit + 本地 Ollama（走 OpenAI 兼容接口）。

回答是一个字一个字蹦出来的（打字机效果），靠 stream=True + st.write_stream 实现。

启动（必须用 streamlit run；直接 python 只会得到一片空白页面）：
    .\\.venv\\Scripts\\Activate.ps1
    streamlit run app.py

前提：本机 Ollama 已启动（127.0.0.1:11434），且已拉取 qwen2.5:7b 模型。
"""

import streamlit as st
from openai import OpenAI

# 模型名只在这里写一次。界面上显示的、发给接口的，都引用这个常量，
# 以后换模型不会出现"界面写着 7b、实际调用 1.5b"这种对不上的情况。
MODEL = "qwen2.5:7b"

# 指向本机 Ollama 的 OpenAI 兼容接口。
# 好处：以后想换成 DeepSeek、通义等云端模型，只需改 base_url 和 api_key，
# 下面的调用代码一行都不用动。本地服务不校验 key，填个占位值即可。
client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")


def init_messages():
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


def stream_text(resp):
    """把“chunk 流”翻译成“纯文字流”。

    参数 resp：create(stream=True) 返回的流对象，每次迭代吐出一个 chunk 对象。
    产生：一个个文字片段（str）。

    为什么必须写成生成器（yield），而不是“攒完再 return”：
        return 要等整个 for 跑完才交出结果，调用方只能干等，打字机效果就没了；
        yield 每产出一块立刻交出去，函数在这里暂停，等调用方要下一块才继续。
    """
    for chunk in resp:
        # 真正的文字藏在 choices[0].delta.content 这一层。
        # 注意是 delta（本次增量），不是 message（整体回答）。
        piece = chunk.choices[0].delta.content
        # 首尾的 chunk 通常没有文字：Ollama 给空字符串，部分厂商给 None。
        # 两者都是 falsy，一个 if 就能同时挡住；漏掉这句会画出空白气泡，
        # 或者对 None 调 len() 直接 TypeError。
        if not piece:
            continue
        yield piece


# Streamlit 每接收一次交互（输入、点按钮）就把整个脚本从头重跑一遍。
# 普通变量每次重跑都会被重置，只有 session_state 里的数据能跨重跑存活。
# 注意：它只活在“当前浏览器会话”里，F5 刷新或关掉标签页就会清空。
if "messages" not in st.session_state:
    st.session_state.messages = init_messages()

st.title("K_ai_D聊天机器人")
st.caption("本地部署 · 数据不出本机")
st.divider()

with st.sidebar:
    st.caption(f"模型: {MODEL}")

    # st.button() 返回 True/False，只有被点击的那一次返回 True，所以要用 if 判断
    if st.button("清空对话"):
        # 重置成一份新的初始对话（含开场问候），再强制重跑一次让界面立刻刷新。
        # 这里必须重新调用 init_messages()，否则问候语会在清空后消失。
        st.session_state.messages = init_messages()
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
    #    stream=True 时，返回的立刻就是一条流，而不是生成完毕的完整回答。
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=st.session_state.messages,
            stream=True,
        )

        # 3) 边收边画。write_stream 消费整条流，一边把文字追加到屏幕上，
        #    一边把拼好的完整回答作为返回值交出来 —— 所以不用自己写 += 去攒。
        with st.chat_message("assistant"):
            full = st.write_stream(stream_text(resp))

        # 4) 入库的是 write_stream 还回来的完整回答，不是某一块碎片。
        #    漏了这句，模型下一轮就不记得自己说过什么，聊几轮就开始重复。
        st.session_state.messages.append({"role": "assistant", "content": full})

    except Exception as e:
        # 失败时把刚入库的用户消息撤回，避免界面留下“半条对话”。
        # 此时 assistant 那条还没入库，所以 pop() 拿掉的正好是 user。
        # st.stop() 中断本次运行，避免后面继续用到未定义的 full。
        st.session_state.messages.pop()
        st.error(f"模型调用失败：{e}")
        st.stop()
