# AGENTS.md

## 项目架构

**单Agent + SOUL注入**：同一个 `agent_loop` 实例通过加载不同的 `souls/{role}/SOUL.md` 展现不同人格（学生/员工/客服）。SOUL.md 仅包含系统提示词 + 工具白名单，不含框架层信息。

```
souls/{student,employee,guest}/SOUL.md  ← SOUL文件（按角色隔离）
app/agent/soul.py          ← SoulManager 加载/解析SOUL
app/agent/auth.py         ← AuthManager JWT注册/登录/验证
app/agent/core.py         ← agent_loop（动态prompt + 工具过滤）
app/rag/router.py         ← KnowledgeRouter（按角色过滤RAG）
```

## 关键依赖

| 包 | 用途 |
|-----|------|
| `uv` | **必须用 `uv sync` / `uv add`**，不是 pip |
| `sqlmodel` | ORM 模型（不是 sqlalchemy，SQLModel.metadata.create_all 建表）|
| `anthropic` | LLM 调用 |
| `chromadb` | 向量存储 |
| `pyjwt` + `bcrypt` | JWT 鉴权 |
| `fastapi` | Web + SSE 流式 |

## 常用命令

```bash
# 安装依赖
uv sync

# 启动服务（开发）
uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# 单独运行测试（各文件独立，无跨文件依赖）
uv run pytest tests/test_auth.py -v
uv run pytest tests/test_soul.py -v
uv run pytest tests/test_knowledge_router.py -v

# 添加依赖（用uv，不要手动编辑pyproject.toml）
uv add <package>

# 初始化/重建数据库表
uv run python -c "from app.db.connection import init_db; init_db()"
```

## 数据库注意事项

- MySQL 连接**必须**加 `--default-character-set=utf8mb4`，否则中文插入报错 `ERROR 1366`
- 模型定义在 `app/db/models.py`（SQLModel，不是 Flask-SQLAlchemy）
- 建表用 `SQLModel.metadata.create_all(engine)`，不是 alembic
- `app/db/connection.py` 的 `init_db_on_startup()` 启动时自动建表（ignore 失败）

## 前端资源

- 静态文件在 `app/api/static/`（index.html, login.html, app.js）
- 登录页：`/login`；聊天页：`/`
- 前端**无状态**，会话由后端 `SessionManager` 管理
- 会话文件存储在 `.conversations/`（运行时创建），格式为 `{id}.json`

## 测试

- 测试文件在 `tests/`（被 .gitignore 忽略）
- `tests/conftest.py` 提供 SQLite 内存数据库 fixture
- `_clean_tool_registry` fixture 自动清理工具注册表，防止测试间污染

## 环境变量（必需）

```
LLM_BASE_URL      # LLM API端点
LLM_AUTH_TOKEN    # API密钥
MODEL_ID          # 模型名，如 qwen3.6-plus
JWT_SECRET_KEY    # JWT签名密钥（生产必须改，代码中未在 .env.example 提供）
EMBEDDINGS_API_KEY # 向量嵌入
DATABASE_HOST/PORT/USER/PASSWORD/NAME  # MySQL
```

## 架构注意事项

- `ToolRegistry.list(allowed_tools=[...])` — 工具过滤参数，None 表示全部
- `ToolRegistry.register_all(tool_defs, enabled)` — 批量注册时先清空再注册，用于 SOUL 切换
- `KnowledgeRouter.build_where_filter()` — 返回 Chroma metadata 过滤条件，实现角色级RAG隔离
- `agent_loop(messages, stream_callback=...)` — 传回调启用 SSE 流式，否则同步阻塞
- SOUL切换时自动更新 system prompt 和工具白名单，无需重启服务