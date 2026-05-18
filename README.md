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
│   │   ├── sessions.py  # 会话管理端点
│   │   ├── notifications.py # 通知端点
│   │   ├── upload.py    # 文件上传端点
│   │   └── auth.py      # 登录注册端点
│   └── static/          # 前端静态资源（无状态 UI + 侧边栏）
├── agent/                # Agent 核心
│   ├── core.py          # agent_loop（流式支持）, TodoManager, SkillLoader
│   ├── session.py       # SessionManager（内存 + 磁盘持久化）
│   ├── soul.py          # SoulManager（SOUL加载/解析）
│   ├── auth.py          # AuthManager（JWT注册/登录/验证）
│   └── tools/           # 工具实现
│       ├── registry.py  # 工具注册表
│       ├── bash.py      # Shell 命令工具
│       ├── file.py      # 文件操作工具
│       ├── rag.py       # RAG 知识搜索
│       ├── dbman.py     # 自然语言数据库操作（NL2SQL）
│       ├── nl2sql.py    # NL2SQL 引擎
│       ├── sql_validator.py # SQL 验证器
│       ├── notify.py    # 通知写入
│       └── report_generator.py # 报告生成
├── db/                   # 数据库层
│   ├── models.py        # SQLModel 模型（15张表）
│   ├── connection.py   # MySQL 连接管理
│   └── seed_data.py    # 种子数据
├── rag/                  # RAG 层
│   ├── embedder.py     # Embedding 服务
│   ├── store.py        # Chroma 向量存储
│   ├── router.py       # KnowledgeRouter（角色级RAG隔离）
│   └── faq_index.py    # FAQ 索引
└── reports/              # 报告生成层
    ├── base.py          # 报告基类
    └── generators/      # 报告生成器（员工日报/客户分析/心理周报/投诉周报）
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
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME` - MySQL
- `EMBEDDINGS_BASE_URL` - 向量嵌入端点
- `EMBEDDINGS_API_KEY` - 向量嵌入密钥
- `EMBEDDINGS_MODEL` - 向量嵌入模型

### 2. 安装依赖

```bash
uv sync
```

### 2.1 文件解析工具（可选）

客户研判功能需要 markitdown 解析文件：

```bash
uv tool install "markitdown[docx,pptx,xlsx,pdf]"
```

### 3. 启动服务

```bash
uv run uvicorn app.api.main:app --reload
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
| `knowledge_search` | 搜索知识库（按角色过滤） |
| `dbman` | 自然语言数据库操作（NL2SQL） |
| `notify` | 写入通知记录 |
| `generate_report` | 生成智能报告（仅 employee 角色） |
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

项目使用 SQLModel，共有 15 张表：User, Course, Event, Registration, Lead, LeadFollowUp, DailyReport, Complaint, Organization, StudentGrade, LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning, Notification。

初始化数据库：
```bash
uv run python -c "from app.db.connection import init_db; init_db()"
```
或手动连接 MySQL（必须加 `--default-character-set=utf8mb4`）：
```bash
mysql -u root -p --default-character-set=utf8mb4
source app/db/init_db.sql;
```

> **注意**：必须使用 `--default-character-set=utf8mb4` 参数连接 MySQL，否则插入中文数据时会报 `ERROR 1366 (HY000): Incorrect string value` 错误。

### RAG 知识库

知识搜索使用 Chroma 向量数据库和 Embedding 服务。文档被嵌入存储，需要配置 `EMBEDDINGS_API_KEY` 和 `EMBEDDINGS_BASE_URL`。

### SOUL 角色系统

Agent 通过加载不同的 SOUL 文件展现不同人格：

| 角色 | SOUL 文件 | 可用工具 |
|------|-----------|---------|
| student | `souls/student/SOUL.md` | knowledge_search, dbman, notify |
| employee | `souls/employee/SOUL.md` | knowledge_search, dbman, generate_report, notify |
| guest | `souls/guest/SOUL.md` | knowledge_search, dbman |

- `souls/tool_config.yaml` 控制每个角色可用的工具
- `souls/nl2sql/tables.yaml` 定义角色可访问的数据库表（employee 15张 / student 11张）
- SOUL切换时自动更新 system prompt 和工具白名单，无需重启服务

### 报告生成（仅 employee）

`generate_report` 工具调用以下生成器：
- `全域客户经营分析报告`（customer_analysis）
- `员工工作日报`（daily_report_summary）
- `心理周报`（psychology_weekly）
- `投诉周报`（complaint_weekly）

## License

MIT