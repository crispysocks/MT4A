# mt4a - Model Toolkit for Agents

一个独立的 AI 编码代理工具包，支持工具调用、任务跟踪和对话上下文管理。

## 功能特性

- **Agent Loop**: 主事件循环，支持流式和同步模式，交替执行 LLM 调用和工具执行
- **Session Manager**: 后端会话管理，内存缓存 + 磁盘持久化，前端无状态
- **Tool Registry**: 可配置的模块化工具注册系统
- **Todo Manager**: 内存任务跟踪，3 轮无更新时自动提醒
- **Context Compression**: 上下文压缩（微压缩 + 自动压缩）
- **FastAPI + SSE**: 支持流式输出的 Web API
- **RAG 知识库**: 基于 Chroma + DashScope Embedding 的知识检索
- **MySQL 数据库**: 通过自然语言查询数据库

## 目录结构

```
app/
├── api/                  # FastAPI Web 层
│   ├── main.py           # FastAPI 入口
│   ├── routes/
│   │   ├── chat.py      # SSE 聊天端点（使用 SessionManager）
│   │   └── sessions.py  # 会话管理端点
│   └── static/          # 前端静态资源（无状态 UI + 侧边栏）
├── agent/                # Agent 核心
│   ├── core.py          # agent_loop（流式支持）, TodoManager, SkillLoader
│   ├── session.py       # SessionManager（内存 + 磁盘持久化）
│   └── tools/           # 工具实现
│       ├── registry.py  # 工具注册表
│       ├── bash.py      # Shell 命令工具
│       ├── file.py      # 文件操作工具
│       ├── rag.py       # RAG 知识搜索
│       └── db.py        # 数据库查询
├── db/                   # 数据库层
│   ├── models.py        # SQLModel 模型
│   └── connection.py   # MySQL 连接管理
└── rag/                  # RAG 层
    ├── embedder.py     # DashScope Embedding
    └── store.py        # Chroma 向量存储
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 密钥
```

必需的环境变量：
- `LLM_BASE_URL` - API 端点
- `LLM_AUTH_TOKEN` - API 密钥
- `MODEL_ID` - 模型标识符

可选：
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME`
- `DASHSCOPE_API_KEY`

### 2. 安装依赖

```bash
uv sync
```

### 3. 启动服务

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看 Web 界面。

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/chat` | POST | 发送消息，接收 SSE 流 |
| `/api/sessions` | GET | 列出所有会话 |
| `/api/sessions/{id}` | GET | 加载指定会话的历史记录 |

### 请求格式

```json
// POST /api/chat
{
  "conversation_id": "可选，不传则创建新会话",
  "message": "用户消息内容"
}
```

### SSE 响应格式

```
data: {"type": "conversation_id", "conversation_id": "..."}
data: {"type": "content", "content": "流式文本片段"}
data: {"type": "done"}
```

## 可用工具

| 工具 | 描述 |
|------|------|
| `bash` | 执行 Shell 命令 |
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件内容 |
| `edit_file` | 编辑文件（精确文本替换） |
| `knowledge_search` | 搜索知识库 |
| `db_query` | 查询数据库 |
| `TodoWrite` | 更新任务跟踪列表 |
| `load_skill` | 加载技能文档 |
| `compress` | 手动压缩对话上下文 |

## 开发

```bash
# 运行测试
uv run pytest tests/ -v

# 添加新依赖（使用 uv，不要直接编辑 pyproject.toml）
uv add <package>
```

## 架构说明

### Session Manager

会话状态完全由后端管理：
- `SessionManager` 在内存中维护活跃会话 `{conversation_id: messages}`
- 每次交互后自动持久化到 `.conversations/{id}.json`
- 收到 `conversation_id` 时从磁盘恢复历史
- 前端无状态，只需发送 `{conversation_id?, message}`

### Streaming Agent Loop

`agent_loop(messages, stream_callback=...)` 支持两种模式：
- **流式模式**：提供 `stream_callback` 时，每次 LLM 输出 token 时调用回调
- **同步模式**：不提供回调时，保持原有阻塞行为（用于 CLI/调试）

Chat 路由使用 `asyncio.Queue` + 后台线程实现真正的实时流式传输。

### Tool Registry

工具通过 `@tool` 装饰器或 `registry.register()` 注册：

```python
from app.agent.tools import registry, tool

# 使用装饰器
@tool(name="my_tool", description="My tool", schema={"type": "object"})
def my_handler():
    return "result"

# 或直接注册
registry.register("my_tool", my_handler, {"type": "object"}, "My tool")
```

### 数据库模型

项目包含三个主要模型：`Course`（课程）、`Event`（活动）、`Registration`（报名）。

### RAG 知识库

知识搜索使用 Chroma 向量数据库和 DashScope Embedding。文档被嵌入存储，需要配置 `DASHSCOPE_API_KEY`。

## License

MIT