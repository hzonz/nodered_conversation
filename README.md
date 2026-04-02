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
`msg.payload.event.request_id: `本次对话唯一 ID (必须在回复时带回)。

2. 返回响应 (Output)
使用 fire event 节点：
事件类型: `nodered_response_event`
数据 (Data):

```
{
  "request_id": "{{payload.event.request_id}}",
  "response": "这是我的回复内容"
}
```

4. 示例 Function 逻辑
如果你需要处理逻辑，可以在中间加一个 function 节点：

```
const { request_id, text } = msg.payload.event;

// 处理你的逻辑
let reply = "你刚才说的是：" + text;

// 构造返回
msg.payload = {
    data: {
        request_id: request_id,
        response: reply
    }
};
return msg;
```

#📝 提示
