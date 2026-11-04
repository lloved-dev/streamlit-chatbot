# 本地聊天机器人（Streamlit + Ollama）

一个跑在自己电脑上的聊天机器人：**模型本地运行，对话数据不出本机，不花钱，断网也能用。**

这是我学习「大模型开发」路线的第 1 个作品，用来打通「调用模型 → 管理对话历史 → 渲染界面」这条链路。

## 界面

![界面截图](docs/screenshot.png)

## 功能

- **多轮对话**：历史存在 `st.session_state`，模型每轮收到完整上下文
- **一键清空**：侧边栏按钮重置对话
- **失败兜底**：模型没启动 / 模型名写错时给出友好提示，并撤回刚发出的那条消息，不留"半条对话"
- **可换后端**：走 OpenAI 兼容接口（`/v1/chat/completions`），换成云端模型只需改 `base_url`

## 技术栈

| 组件 | 说明 |
|---|---|
| Python 3.14 | |
| Streamlit 1.66 | Web 界面 |
| Ollama | 本地模型运行时 |
| openai SDK | 通过 OpenAI 兼容接口调用本地模型 |

## 运行

前提：本机已安装并启动 [Ollama](https://ollama.com)，且已拉取模型。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

ollama pull qwen2.5:7b

streamlit run app.py
```

浏览器打开 http://localhost:8501 。

> 必须用 `streamlit run app.py` 启动，直接 `python app.py` 页面会是空白的。

## 文件说明

| 文件 | 作用 |
|---|---|
| `app.py` | 主程序：界面 + 对话历史 + 模型调用 |
| `demo.py` | 命令行最小示例，演示 `messages` 结构和多轮上下文 |
| `requirements.txt` | 依赖版本 |

## 几个踩过的坑（写给自己看）

1. **`st.session_state` 只活在当前会话里**：脚本重跑（输入、点按钮）时保留，浏览器 F5 刷新就清空。想持久化得写文件或数据库。
2. **Streamlit 是自上而下执行一次**：新消息 `append` 之后必须当场画一遍气泡，否则要等下一次交互才显示，永远"慢一拍"。
3. **模型的回答也要存进历史**：只存用户的话，模型就不记得自己说过什么，聊两轮开始重复。
4. **`st.button()` 返回布尔值**：必须 `if st.button(...)`，不能像 `if`/`for` 那样直接跟冒号。

## 后续可以做的

- [ ] 流式输出（打字机效果，`stream=True`）
- [ ] 只保留最近 N 轮历史，避免超出上下文长度
- [ ] 多会话管理 + 落盘保存
- [ ] 换个界面主题 / 加头像