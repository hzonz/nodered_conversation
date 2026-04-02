#Node-RED Conversation Agent

这是一个将 Home Assistant (HA) 的 Assist 语音助手 对话请求转发至 Node-RED 处理的自定义集成。

##🌟 集成简介
本集成让 Node-RED 成为 HA 的语音助手“大脑”。
异步机制：采用 HA 事件总线通讯，支持长耗时任务（如 ChatGPT）。
灵活性高：支持通过 Node-RED 自由控制回复时机（对话框回复或音箱 TTS 播报）。

##📦 安装方式 (HACS)
打开 HACS -> 集成 (Integrations)。
点击右上角三个点，选择 自定义存储库 (Custom repositories)。
输入本仓库的 GitHub 地址，类别选择 集成 (Integration)。
点击 下载，安装完成后 重启 Home Assistant。
前往 设置 -> 设备与服务 -> 添加集成，搜索并添加 Node-Red Conversation Agent。
前往 设置 -> 语音助手 (Assist)，将 对话代理 切换为 Node-Red Async Agent。

##🛠️ Node-RED 接入方式
集成通过两个核心事件与 Node-RED 通讯：
1. 接收请求 (Input)
使用 events: all 节点：
事件类型: nodered_request_event
关键内容:
msg.payload.event.text: 用户说的文字。
msg.payload.event.request_id: 本次对话唯一 ID (必须在回复时带回)。
2. 返回响应 (Output)
使用 fire event 节点：
事件类型: nodered_response_event
数据 (Data):
code
JSON
{
  "request_id": "{{payload.event.request_id}}",
  "response": "这是我的回复内容"
}
3. 示例 Function 逻辑
如果你需要处理逻辑，可以在中间加一个 function 节点：
code
JavaScript
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

#📝 提示
