# Node-RED Conversation Agent

这是一个将 Home Assistant (HA) 的 Assist 语音助手 对话请求转发至 Node-RED 处理的自定义集成。

## 🌟 集成简介

- 本集成让 Node-RED 成为 HA 的语音助手“大脑”。
- 异步机制：采用 HA 事件总线通讯，支持长耗时任务（如 ChatGPT）。
- 灵活性高：支持通过 Node-RED 自由控制回复时机（对话框回复或音箱 TTS 播报）。

## 📦 安装方式

### 使用 HACS（推荐）

1. 打开 Home Assistant 的 HACS 页面  
2. 点击右上角 **“添加存储库 (Custom Repository)”**  
3. 填入仓库 URL:  
```yaml
https://github.com/hzonz/nodered_conversation
```
4. 类型选择 **Integration**，然后添加  
5. 搜索 **Node-Red Conversation Agent** 并安装，完成后重启。
6. 前往 设置 -> 设备与服务 -> 添加集成，搜索并添加 Node-Red Conversation Agent。
7. 前往 设置 -> 语音助手 (Assist)，将 对话代理 切换为 Node-Red Async Agent。

## 🛠️ Node-RED 接入方式

集成通过两个核心事件与 Node-RED 通讯：

1. 接收请求 (Input)
使用 events: all 节点：
事件类型: `nodered_request_event`
关键内容:
`msg.payload.event.text:` 用户说的文字。
`msg.payload.event.conversation_id: `本次对话唯一 ID (必须在回复时带回)。

3. 返回响应 (Output)
使用 fire event 节点：
事件类型: `nodered_response_event`
数据 (Data):

```
{
  "request_id": "{{payload.event.conversation_id}}",
  "response": "这是我的回复内容"
}
```

4. 示例 Function 逻辑
如果你需要处理逻辑，可以在中间加一个 function 节点：

```

// 1. 获取从 HA 传过来的原始数据 (nodered_request_event)
const eventData = msg.payload.event;

// 2. 提取核心标识 优先使用 conversation_id
// 我们在 Python 中确保了这两个字段都会发过来
const convId = eventData.conversation_id;
const userText = eventData.text || ""; 
const userId = eventData.user_id;

// 3. 编写逻辑处理
let replyText = "";
let shouldContinue = false; // 默认不保持对话

if (userText.includes("你好")) {
    replyText = "你好！我是 Node-RED 智能管家。请问有什么我可以帮您的？";
    shouldContinue = true; // 开启对话保持，等待用户下一句
} else if (userText.includes("时间")) {
    replyText = "当前时间：" + new Date().toLocaleString();
    shouldContinue = false; // 回答完毕，关闭对话
} else if (userText.includes("你是谁")) {
    // 演示使用透传的 user_id
    replyText = `我是由 Node-RED 驱动的助手。识别到您的用户 ID 为：${userId || "未知"}`;
    shouldContinue = true;
} else {
    replyText = "指令已收到。";
    shouldContinue = false;
}

// 4. 必须确保 event.data 中包含以下字段，以便 Python 中的 Future 能正确匹配
msg.payload = {
    "conversation_id": convId,      // 必须带回，用于匹配 Future 注册表
    "response": replyText,          // 最终显示给用户的文字
    "continue_conversation": shouldContinue // 2026 重构重点：是否让微信/助手继续等待输入
};

// 5. 返回消息给 HA 的 'Fire Event' 节点
// 目标事件名应设为：nodered_response_event
return msg;
```

# 📝 提示
暂无
