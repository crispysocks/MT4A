# mt4a 架构重构设计方案

## 概述

将单文件 `agent/agent.py` 重构为多层架构，支持 FastAPI Web UI、知识库检索（RAG）和数据库操作。

## 技术选型

- **API**: FastAPI + SSE 流式响应
- **Agent**: 重构为分层模块，单进程部署
- **RAG**: Chroma + 云服务 Embedding（DashScope）
- **Database**: MySQL + SQLModel/SQLAlchemy

## 目录结构

```
app/
├── api/                      # FastAPI 应用层
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── routes/              # REST 路由
│   │   ├── __init__.py
│   │   └── chat.py         # SSE 聊天路由
│   └── static/             # 静态文件（HTML/JS/CSS）
├── agent/                   # Agent 核心
│   ├── __init__.py
│   ├── core.py             # agent_loop, message handling
│   ├── tools/              # Tool 实现
│   │   ├── __init__.py
│   │   ├── registry.py     # Tool 注册表（装饰器方式）
│   │   ├── bash.py         # Shell 命令执行
│   │   ├── file.py         # 文件读写编辑
│   │   ├── rag.py          # Chroma 知识库检索
│   │   └── db.py           # 数据库语义操作
│   └── compress/           # 上下文压缩
├── db/                     # 数据库层
│   ├── __init__.py
│   ├── models.py           # SQLModel 模型定义
│   └── connection.py       # MySQL 连接管理
├── rag/                    # RAG 核心
│   ├── __init__.py
│   ├── embedder.py        # Embedding 生成（DashScope）
│   └── store.py           # Chroma 存储/检索
└── skills/                 # Skill 文件
    └── SKILL.md
```

## 核心组件设计

### 1. Tool 注册机制 (`agent/tools/registry.py`)

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, name: str, handler: Callable, schema: dict, description: str)
    def list(self) -> list[dict]  # 返回工具列表
    def get_handler(self, name: str) -> Callable

# 装饰器方式注册
registry = ToolRegistry()

def tool(name: str, description: str, schema: dict):
    def decorator(fn: Callable):
        registry.register(name, fn, schema, description)
        return fn
    return decorator
```

**配置方式**：在 `agent/tools/__init__.py` 中统一注册可用 tools

### 2. RAG 层 (`rag/`)

**索引来源**：`knowledge/processed/` 下的 `.md` 文件
- `business/` - 业务相关
- `company/` - 公司信息
- `policy/` - 留学政策

**索引流程**（初始化时）：
```
knowledge/processed/*.md → 读取 → 分块 → embedder → Chroma collection
```

**检索流程**（tool 调用时）：
```
query → embedder → Chroma.query → 返回文本片段
```

**Embedding**：使用 DashScope 云服务 API

### 3. 数据库层 (`db/`)

**表结构**：

| 表名 | 用途 | 说明 |
|------|------|------|
| `courses` | 课程/项目信息 | 含类型、国家、费用、招生对象等16条初始数据 |
| `events` | 活动/讲座排期 | 含时间、地点、类型、状态，6条初始数据 |
| `registrations` | 用户报名记录 | 外键关联 events，运行时写入 |

**Tool**：`db_query` tool，接收自然语言参数，生成并执行 SQL

### 4. API 层 (`api/`)

- **SSE 流式响应**：POST `/chat` 返回 SSE 流
- **静态文件挂载**：`/static` 路径下 HTML/CSS/JS
- **健康检查**：`GET /health`

### 5. Agent Core (`agent/core.py`)

保留原 `agent.py` 的核心逻辑：
- `agent_loop`: 主循环
- `microcompact`: 每轮清理旧 tool_result
- `auto_compact`: 超阈值时压缩

## 数据流

```
用户请求 → FastAPI (HTTP/SSE)
         → Agent Loop
         → Tool 执行 (RAG / DB / Bash / File)
         → SSE 流式返回
```

## 实现顺序

1. **第 1 步**：重构 agent/ 为多层结构（tools/registry + tools 实现）
2. **第 2 步**：添加 FastAPI + SSE 聊天接口
3. **第 3 步**：集成 RAG（Chroma + DashScope embedding）
4. **第 4 步**：添加数据库层（MySQL + db tool）
5. **第 5 步**：前端静态页面

## 环境变量

| 变量 | 描述 |
|------|------|
| `LLM_BASE_URL` | API endpoint |
| `LLM_AUTH_TOKEN` | API key |
| `MODEL_ID` | 模型标识 |
| `DATABASE_HOST` | MySQL 主机 |
| `DATABASE_PORT` | MySQL 端口 |
| `DATABASE_USER` | MySQL 用户 |
| `DATABASE_PASSWORD` | MySQL 密码 |
| `DATABASE_NAME` | 数据库名 |
| `DASHSCOPE_API_KEY` | Embedding API key |

## 部署

- 单进程部署，无需 Docker
- 静态 HTML 页面挂载于 FastAPI

## 排除内容

- `references/` 目录：不参与项目构建，仅作参考
- `knowledge/raw/`：不索引
- `knowledge/整理思路.md`：不索引