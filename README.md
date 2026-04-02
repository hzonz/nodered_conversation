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

3. 返回响应 (Output)
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
// 1. 获取从 HA 传过来的原始数据
const eventData = msg.payload.event;

// 2. 提取 request_id (对话ID，必需项)
const requestId = eventData.request_id;
const userText = eventData.text; // 用户说的话

// 3. 编写你的逻辑处理
let replyText = "";

if (userText.includes("你好")) {
    replyText = "你好！我是你的 Node-RED 智能管家。";
} else if (userText.includes("时间")) {
    replyText = "现在是北京时间：" + new Date().toLocaleString();
} else {
    replyText = "我已经收到指令：'" + userText + "'，正在处理中...";
}

// 4. 构造发送给 HA 'fire event' 节点的数据包
// 注意：如果你在 Fire Event 节点里配置了 Data 留空，
// 那么这里必须把数据放在 msg.payload 中
msg.payload = {
    "request_id": requestId,
    "response": replyText
};

// 5. 返回消息
return msg;
```

# 📝 提示
暂无
