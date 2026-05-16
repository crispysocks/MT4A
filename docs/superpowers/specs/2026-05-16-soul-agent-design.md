# 单Agent多角色SOUL注入系统 设计文档

## 概述

本项目将现有 `mt4a` 单Agent框架改造为一个 **身份驱动认知注入** 系统。通过 `SOUL.md` 文件动态切换Agent的认知、功能和服务方向，用户视角看到多个不同的Agent，底层是同一个Agent实例。

### 核心创新点

单Agent + SOUL注入：用户登录后，系统根据账户角色自动加载对应的 SOUL.md（系统提示词 + 工具白名单），使同一个Agent实例展现完全不同的"人格"。

---

## 角色定义

| 角色 | 标识 | 主题色 | 访问方式 | 说明 |
|------|------|--------|---------|------|
| 学生 | `student` | 蓝色 | 登录 | 面向学生的智能助手 |
| 员工/老师 | `employee` | 绿色 | 登录 | 面向员工的智能助手 |
| 客服（游客） | `guest` | 灰色 | 免登录 | 对外客服咨询 |

---

## 架构设计

### 整体架构

```
前端 (static/)
├── 登录/注册页 (/login)
└── 聊天页 (/)
    ├── 顶部栏（主题色 + 登出）
    ├── 左侧：历史对话列表 + 新建对话
    └── 右侧：聊天界面

FastAPI 路由层
├── /api/auth/login   → AuthManager.login()
├── /api/auth/register → AuthManager.register()
├── /api/auth/logout  → AuthManager.logout()
├── /api/auth/me      → AuthManager.verify()
├── /api/chat         → agent_loop (SSE 流式)
└── /api/sessions/*   → SessionManager

核心层
├── SoulManager（新）
│   ├── load(role) → 解析 SOUL.md
│   ├── get_system_prompt() → 当前 prompt
│   ├── get_tools() → 当前工具白名单
│   └── unload() → 清空当前 SOUL
├── AuthManager（新）
│   ├── login() / register() / logout()
│   └── verify() → JWT 验证
├── agent_loop（改造）
│   ├── 从 SoulManager 获取 system prompt（替代硬编码 SYSTEM）
│   └── 从 SoulManager 获取工具列表并过滤 registry.list()
├── ToolRegistry（现有，改造）
│   └── list(allowed_tools) → 按白名单过滤
└── KnowledgeRouter（新，RAG 层改造）
    └── 按角色过滤知识库检索范围
```

### 核心流程

```
用户登录 → AuthManager 验证 → 返回角色
→ SoulManager.load(role) → 解析 souls/{role}/SOUL.md
→ agent_loop 获取 system prompt + 工具列表
→ 用户发消息 → Agent 以该角色身份响应
→ 登出 → SoulManager.unload() → 回到默认/空状态
```

---

## SOUL.md 设计

### 文件位置

```
souls/
├── student/SOUL.md
├── employee/SOUL.md
└── guest/SOUL.md
```

### 文件格式（Frontmatter + 正文）

```markdown
---
name: 学生智能助手
role: student
tools: [db_query, rag, todo_write, leave_request, complaint_submit, compress]
---

你是XX留学机构的学生智能助手，负责帮助留学生处理日常事务...
（完整的 system prompt 正文，仅包含大模型需要知道的认知信息）
```

### 设计原则

- SOUL.md 只包含 **系统提示词 + 工具白名单**，不包含框架层信息（知识库范围、数据库连接等）
- 知识库隔离、数据表权限等由框架层（KnowledgeRouter、SoulManager）统一管理
- 新增角色只需在 `souls/` 下新建目录 + SOUL.md 文件

### SoulManager 职责

| 方法 | 说明 |
|------|------|
| `load(role: str)` | 读取 `souls/{role}/SOUL.md`，解析 frontmatter，缓存 prompt 和 tools |
| `get_system_prompt()` | 返回当前激活的 system prompt |
| `get_tools()` | 返回当前允许的工具名列表 |
| `unload()` | 清空当前 SOUL，重置为默认状态 |
| `is_active()` | 是否有 SOUL 激活 |

SoulManager 为单例，全局同时只有一个激活的 SOUL。

---

## 鉴权设计

### AuthManager

- `register(username, password, role)` → 创建用户，bcrypt 加密密码
- `login(username, password)` → 验证，返回 JWT token + role
- `logout()` → 清除当前 SOUL + 会话
- `verify(token)` → 验证 token，返回用户信息

### 用户表

```sql
users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'employee') NOT NULL,  -- 注册时自选
    created_at DATETIME DEFAULT NOW()
)
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 注册（username, password, role） |
| `/api/auth/login` | POST | 登录（username, password）→ token + role |
| `/api/auth/logout` | POST | 登出，清除 SOUL |
| `/api/auth/me` | GET | 验证当前 token |

### 鉴权流程

1. 所有需要登录的API端点通过 JWT 中间件验证
2. 登录成功后前端存储 token，后续请求携带 `Authorization: Bearer <token>`
3. 游客（客服）无需 token，`/api/chat` 对未认证请求自动加载 `guest` SOUL

---

## 数据库设计

### 现有表（保留）

- `courses` — 课程项目
- `events` — 活动/讲座
- `registrations` — 活动报名

### 新增表

#### 认证
```sql
users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'employee') NOT NULL,
    created_at DATETIME DEFAULT NOW()
)
```

#### CRM / 意向客户
```sql
leads (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(100),
    source VARCHAR(100),
    status ENUM('new','contacted','negotiating','signed','lost') DEFAULT 'new',
    assigned_to INT,
    notes TEXT,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
)

lead_follow_ups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    lead_id INT NOT NULL,
    content TEXT NOT NULL,
    follow_type VARCHAR(50),
    created_by INT,
    created_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
)
```

#### 运营管理
```sql
daily_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    department VARCHAR(100),
    submitted_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
)

complaints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    category VARCHAR(100),
    content TEXT NOT NULL,
    status ENUM('pending','processing','resolved','closed') DEFAULT 'pending',
    handler_id INT,
    resolution TEXT,
    created_at DATETIME DEFAULT NOW(),
    resolved_at DATETIME,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (handler_id) REFERENCES users(id)
)

organization (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    type ENUM('department', 'person') NOT NULL,
    parent_id INT,
    contact_info VARCHAR(255),
    FOREIGN KEY (parent_id) REFERENCES organization(id)
)
```

#### 教务管理
```sql
student_grades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    grade VARCHAR(20),
    semester VARCHAR(50),
    recorded_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES users(id)
)

leave_requests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    reason TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    approver_id INT,
    approved_at DATETIME,
    created_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
)

exam_schedule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    type VARCHAR(100),
    subject VARCHAR(100),
    deadline DATETIME,
    description TEXT,
    FOREIGN KEY (student_id) REFERENCES users(id)
)
```

#### 心理关怀
```sql
psychology_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    emotion_tag VARCHAR(100),
    score INT,
    notes TEXT,
    recorded_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES users(id)
)

psychology_warnings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    trigger_reason TEXT NOT NULL,
    risk_level ENUM('low','medium','high','critical') DEFAULT 'medium',
    status ENUM('active','acknowledged','resolved') DEFAULT 'active',
    handler_id INT,
    created_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (handler_id) REFERENCES users(id)
)
```

### 表说明（不建表）

以下需求通过查询聚合或文件处理实现，不需独立建表：
- **智能报告**：从上述业务表聚合查询 + LLM 生成
- **客户研判**：文件解析 + 规则匹配（即时处理，不持久化）

---

## 知识库设计

### 知识库结构

```
knowledge/
├── raw/                        # 原始文件
│   ├── 公司信息/
│   │   ├── 企业信息.md          # → company/public
│   │   ├── 常见问答对.md        # → company/public
│   │   └── 公司新人指南.md      # → company/internal
│   ├── 公司业务/
│   │   ├── 中德精英人才共建计划.md  # → business
│   │   └── 新加坡国际本硕升学计划.md # → business
│   └── 留学政策/
│       ├── 德国留学政策指南.md  # → policy
│       └── 新加坡留学政策指南.md # → policy
└── processed/                  # 已预处理的分片
    ├── company/
    │   ├── brand.md            # public
    │   ├── campuses.md         # public
    │   ├── faq.md              # public
    │   └── history.md          # internal
    ├── business/
    │   ├── enhancement.md
    │   └── study_abroad.md
    └── policy/
        ├── germany.md
        └── singapore.md
```

### 知识库分层

| 层级 | 内容 | guest | student | employee |
|------|------|-------|---------|----------|
| company/public | 品牌、校区、对外FAQ | ✓ | ✓ | ✓ |
| company/internal | 新人指南、内部制度 | ✗ | ✗ | ✓ |
| business | 升学计划、项目 | ✓ | ✓ | ✓ |
| policy | 留学政策 | ✓ | ✓ | ✓ |

### KnowledgeRouter

在现有 RAG 层新增 `KnowledgeRouter`，根据当前激活的角色过滤检索范围：

- `get_allowed_bases()` → 返回当前角色可检索的知识库列表
- `knowledge_search` 工具调用时传入允许的 knowledge_base 列表
- SOUL.md 中不包含知识库范围信息，由 KnowledgeRouter 统一管理

---

## 前端设计

### 页面

**登录/注册页** (`/login`):
- 登录表单：用户名 + 密码
- 注册表单：用户名 + 密码 + 角色选择（学生/员工）
- 客服入口："无需登录，直接咨询"按钮
- 登录成功 → 跳转到聊天页

**聊天页** (`/`):
- 顶部栏：主题色（蓝/绿/灰），登出按钮
- 左侧边栏：历史对话列表，新建对话按钮
- 右侧主区域：聊天界面（复用现有UI）
- 游客模式：无登出按钮，显示"登录享受更多功能"

### 主题色

| 角色 | 颜色 |
|------|------|
| student | 蓝色 `#2563eb` |
| employee | 绿色 `#16a34a` |
| guest | 灰色 `#6b7280` |

---

## 技术栈

- Python 3.12+
- FastAPI（Web框架）
- SQLModel + MySQL（数据库）
- Anthropic SDK（LLM 调用）
- Chroma + DashScope（向量存储 + 嵌入）
- JWT（鉴权）
- bcrypt（密码哈希）

---

## 实施范围

### 必须实现
- [ ] 用户认证系统（登录/注册/登出/JWT）
- [ ] SoulManager（SOUL.md 加载/解析/卸载）
- [ ] 三份 SOUL.md 文件
- [ ] agent_loop 改造（动态 system prompt + 工具过滤）
- [ ] 数据库表扩展（11张新表）
- [ ] KnowledgeRouter（按角色隔离RAG检索）
- [ ] 前端登录页 + 聊天页改造（主题色）
- [ ] 客服免登录入口

### 不实现
- 多用户并发登录
- 真实外部系统对接
- 定时任务/主动推送
- 智能报告生成（非演示核心）
- 客户研判（文件解析）
