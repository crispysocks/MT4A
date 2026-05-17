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

## 工具配置

- `souls/tool_config.yaml` 控制每个角色可用的工具（编辑后下次请求自动生效）
- `souls/{role}/SOUL.md` 定义角色系统提示词（支持 YAML frontmatter）
- 工具通过 `@tool` 装饰器或 `registry.register()` 注册在 `app/agent/tools/__init__.py`

## Skills 动态加载

- `skills/` 目录由 `SkillLoader` 在运行时动态扫描 `SKILL.md` 文件（当前目录不存在，Agent 调用 `load_skill` 返回 `(no skills)`，不影响其他功能）
- 后续计划添加项目级 SKILL.md 文件

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

## 环境变量（可选）

```
NL2SQL_MAX_TOKENS # NL2SQL LLM调用最大token数，默认2000
TOKEN_THRESHOLD   # 对话上下文压缩阈值，默认100000
WORKDIR           # 工作目录，默认当前目录
```

## 架构注意事项

- `ToolRegistry.list(allowed_tools=[...])` — 工具过滤参数，None 表示全部
- `ToolRegistry.register_all(tool_defs, enabled)` — 批量注册时先清空再注册，用于 SOUL 切换
- `KnowledgeRouter.build_where_filter()` — 返回 Chroma metadata 过滤条件，实现角色级RAG隔离
- `agent_loop(messages, stream_callback=...)` — 传回调启用 SSE 流式，否则同步阻塞
- SOUL切换时自动更新 system prompt 和工具白名单，无需重启服务

## 未完成进度清单

> 说明：每完成一个进度项就将 `[ ]` 改为 `[x]`。详细需求说明见 `docs/PROGRESS.md`。

### P0 - 核心功能

- [x] **1. NL2SQL 自然语言查询**
  - 客户需求：`企业智能助手 → NL2SQL实现：针对上述数据表开发自然语言转SQL功能，支持员工通过口语（如"帮我查一下张三的最近跟进记录"）直接调取数据库信息。`
  - 当前：已完成 `dbman` 工具（`app/agent/tools/dbman.py`），基于 LLM 的 NL2SQL 引擎 + SQL 安全校验层 + 执行器。按角色控制表权限（employee 14张 / student 10张 / guest 4张）。

- [x] **2. 活动报名闭环**
  - 客户需求：`客服Agent → 活动与讲座报名：支持客户查询近期的线上/线下留学分享会、招生官见面会，并直接完成活动预约与报名，有效沉淀私域流量。`
  - 当前：`Event`/`Registration` 表已存在，`dbman` 可操作，guest 角色已开放权限
  - 需新增：前端活动展示UI + 报名交互 + Agent主动推荐逻辑

- [ ] **3. 审批闭环 + 通知机制**
  - 客户需求：`学生智能助手 → 行政服务：支持学生在线提交请假申请，系统自动推送至班主任，并支持通过企业智能助手实现移动端在线审批，形成完整的请假闭环。` + `售后反馈：老师跟进处理完毕后，系统自动向学生同步"您的xxx投诉已解决"的反馈通知。`
  - 当前：`LeaveRequest`/`Complaint` 表支持CRUD
  - 需新增：消息推送机制（WebSocket/SSE/邮件）+ 审批状态变更回调通知

- [ ] **4.1 全域客户经营分析报告**
  - 客户需求：`智能报告 → 全域客户经营分析报告：全面覆盖意向、成交及流失三大核心客群...通过特征聚类精准提炼共性画像...智能归因并预警流失风险。`
  - 当前：完全未实现
  - 需新增：report_generator模块 + 数据分析逻辑 + AI洞察生成

- [ ] **4.2 员工日报汇总报告（日/周）**
  - 客户需求：`智能报告 → 员工日报汇总报告：通过日、周等多维时间粒度，对全员提交的工作内容进行自动化梳理与提炼。系统利用AI智能提取日报中的核心进展、关键产出及潜在风险。`
  - 当前：完全未实现
  - 需新增：定时汇总任务 + AI摘要生成

- [ ] **4.3 学生心理健康周报**
  - 客户需求：`智能报告 → 学生心理健康周报：基于留学生的日常情绪打卡、学业压力反馈及跨文化适应情况，利用AI智能汇总本周整体心理态势，精准识别存在孤独感、学业焦虑或文化冲突等潜在风险的学生群体。`
  - 当前：完全未实现
  - 需新增：情绪趋势分析 + 风险群体识别 + 个性化疏导建议生成

- [ ] **4.4 投诉处理周报**
  - 客户需求：`智能报告 → 投诉处理周报：实时汇总本周的投诉总量及其同环比变化，利用AI对投诉内容进行智能分类...自动识别长期未决的疑难案件并触发预警。`
  - 当前：完全未实现
  - 需新增：投诉统计分析 + 智能分类 + 处理时效追踪

### P1 - 增强功能

- [ ] **5. 主动待办推送**
  - 客户需求：`企业智能助手 → 主动待办推送：配置定时任务或触发器，当系统检测到有待处理事项时，主动询问员工"有没有投诉反馈需要跟进？"或"有没有请假需要审批？"`
  - 当前：无定时任务调度机制
  - 需新增：APScheduler/Celery + 待办检测逻辑 + 主动推送

- [ ] **6. 客户研判**
  - 客户需求：`客户研判 → 基于甲方提供的文件《用户画像研判规则》去判断某一客户信息来源是否符合甲方公司的两个产品的要求。客户信息来源有可能是文本、pdf简历、excel表格等各种形式。`
  - 当前：完全未实现
  - 需新增：文件解析（PDF/Excel）+ 用户画像规则引擎 + 研判报告

- [ ] **7. 智能提醒**
  - 客户需求：`学生智能助手 → 学业考务：并可设置考前或截止前的智能提醒，规避学业风险。`
  - 当前：完全未实现
  - 需新增：定时任务调度 + 提醒通知机制

- [ ] **8. 海外生活知识库数据补充**
  - 客户需求：`学生智能助手 → 生活支持：内置海外生活知识库，提供当地医疗、交通、紧急求助等生活常识问答，做学生身边的本地百事通。`
  - 当前：RAG架构就绪，`knowledge/` 目录中无海外生活数据
  - 需新增：数据准备 + 入库脚本

### P2 - 后续增强

- [ ] **9. 指令式业务处理（专用解析器）**
  - 客户需求：`企业智能助手 → 指令式业务处理：开发基于自然语言的指令解析能力，支持员工直接下达操作指令，如识别"同意张三同学的请假申请"`
  - 当前：已由 `dbman` 替代 `db_query`，LLM 解析自然语言生成 SQL 执行

- [ ] **10. 心理预警自动触发**
  - 客户需求：`学生智能助手 → 风险识别：编写专属Prompt，实时监测闲聊情绪，触发高危预警并自动写入预警表。`
  - 当前：SOUL.md中已定义预警场景，`dbman` 可写入 `PsychologyWarning` 表
  - 需新增：强化SOUL.md提示词 或 自动监测机制

- [ ] **11. 外部系统对接**
  - 客户需求：`学生智能助手 → 系统对接：开发API接口，实时拉取教务系统的DDL数据与CRM系统的申请进度。`
  - 当前：完全未实现
  - 需新增：外部API对接层

- [ ] **12. 投诉工单自动摘要**
  - 客户需求：`学生智能助手 → 智能摘要：自动提炼学生长篇投诉为工单摘要。`
  - 当前：`Complaint` 表无 `summary` 字段
  - 需新增：LLM自动生成摘要逻辑