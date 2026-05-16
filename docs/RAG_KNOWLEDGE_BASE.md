# RAG 知识库制作教程

## 概述

本系统使用 **Chroma** 作为向量数据库，配合 Embedding 服务实现知识检索（RAG）。

```
用户输入 → 嵌入(Embedding) → 向量相似度匹配 → 返回知识片段
```

## 架构组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `Embedder` | `app/rag/embedder.py` | 调用 embedding API 将文本转为向量 |
| `ChromaStore` | `app/rag/store.py` | 封装 Chroma 客户端，提供 `add_documents` / `query` |
| `KnowledgeRouter` | `app/rag/router.py` | 根据用户角色过滤可检索的知识库分区 |
| `knowledge_search` | `app/agent/tools/rag.py` | Agent 工具，调用 store.query 返回结果 |

## 知识库分区设计

通过 `metadata.source` 字段实现角色级隔离：

```python
ROLE_KNOWLEDGE_BASES = {
    "student":  ["company/public", "business", "policy"],      # 学生：只能看公开、业务、政策
    "employee": ["company/public", "company/internal", "business", "policy"],  # 员工：多一个内部
    "guest":    ["company/public", "business", "policy"],      # 访客：同学生
}
```

检索时自动附加 `where` 过滤条件，保证跨角色隔离。

## 制作步骤

### Step 1: 准备知识文档

将知识整理为结构化文本，每条代表一个可独立检索的片段。

示例知识条目：

```
[公司介绍]
公司成立于2010年，专注于教育信息化领域，总部位于北京。

[留学政策]
研究生项目申请截止日期为每年3月31日，需提交成绩单和推荐信。

[内部制度]
员工出差报销标准：国内机票经济舱，实报实销。
```

### Step 2: 创建填充脚本

在项目根目录创建 `scripts/populate_knowledge.py`：

```python
"""知识库填充脚本 - 将文档嵌入向量数据库"""

from app.rag.store import ChromaStore

def populate():
    store = ChromaStore()

    documents = [
        # company/public - 公开信息，全员可见
        {
            "text": "公司成立于2010年，专注于教育信息化领域，总部位于北京。",
            "id": "pub_001",
            "metadata": {"source": "company/public", "type": "about"}
        },
        {
            "text": "公司使命：用技术赋能教育创新。",
            "id": "pub_002",
            "metadata": {"source": "company/public", "type": "mission"}
        },
        {
            "text": "公司地址：北京市海淀区中关村大街1号。",
            "id": "pub_003",
            "metadata": {"source": "company/public", "type": "contact"}
        },

        # company/internal - 内部信息，仅员工可见
        {
            "text": "员工出差报销标准：国内机票经济舱，实报实销，单次上限5000元。",
            "id": "int_001",
            "metadata": {"source": "company/internal", "type": "policy"}
        },
        {
            "text": "考勤规定：上班时间9:00，下班时间18:00，打卡制。",
            "id": "int_002",
            "metadata": {"source": "company/internal", "type": "policy"}
        },

        # business - 业务信息，学生/员工/访客均可见
        {
            "text": "留学申请流程：1.选校 2.准备材料 3.提交申请 4.面试 5.录取",
            "id": "biz_001",
            "metadata": {"source": "business", "type": "process"}
        },
        {
            "text": "语言培训课程：新托福、雅思、SAT、GRE，滚动开班。",
            "id": "biz_002",
            "metadata": {"source": "business", "type": "course"}
        },

        # policy - 政策信息，学生/员工/访客均可见
        {
            "text": "研究生项目申请截止日期：每年3月31日。",
            "id": "pol_001",
            "metadata": {"source": "policy", "type": "deadline"}
        },
        {
            "text": "申请材料清单：成绩单、推荐信2封、个人陈述、护照复印件。",
            "id": "pol_002",
            "metadata": {"source": "policy", "type": "requirements"}
        },
    ]

    texts = [d["text"] for d in documents]
    ids = [d["id"] for d in documents]
    metadatas = [d["metadata"] for d in documents]

    store.add_documents(texts, ids, metadatas)
    print(f"已填充 {len(texts)} 条知识")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)
    populate()
```

### Step 3: 运行填充

```bash
uv run python scripts/populate_knowledge.py
```

输出示例：
```
已填充 9 条知识
```

### Step 4: 验证知识库

```bash
uv run python -c "
from app.agent.tools.rag import knowledge_search
print(knowledge_search('公司介绍'))
"
```

输出示例：
```
Knowledge search results:

[1] (relevance: 0.95)
公司成立于2010年，专注于教育信息化领域，总部位于北京。
```

### Step 5: 验证角色隔离

以不同角色登录，检索 `"出差报销"`：

| 角色 | 可见？ | 说明 |
|------|--------|------|
| `student` | ❌ | source 不在允许列表 |
| `employee` | ✅ | source=company/internal 在允许列表 |
| `guest` | ❌ | source 不在允许列表 |

## metadata.source 可选值

| 值 | 说明 | student可见 | employee可见 | guest可见 |
|-----|------|:-----------:|:------------:|:---------:|
| `company/public` | 公开公司信息 | ✅ | ✅ | ✅ |
| `company/internal` | 内部制度 | ❌ | ✅ | ❌ |
| `business` | 业务信息 | ✅ | ✅ | ✅ |
| `policy` | 政策文件 | ✅ | ✅ | ✅ |

## 维护命令

```bash
# 查看知识库条数
uv run python -c "
import chromadb
c = chromadb.PersistentClient(path='.chroma').get_or_create_collection('knowledge')
print('Total:', c.count())
"

# 清空知识库（重新开始）
uv run python -c "
import chromadb
c = chromadb.PersistentClient(path='.chroma').get_or_create_collection('knowledge')
c.delete(where={})
print('Cleared')
"

# 导出所有知识
uv run python -c "
import chromadb
c = chromadb.PersistentClient(path='.chroma').get_or_create_collection('knowledge')
for doc, meta in zip(c.get()['documents'], c.get()['metadatas']):
    print(f\"[{meta['source']}] {doc[:80]}...\")
"
```

## 目录结构

```
.
├── .chroma/                    # Chroma 向量数据库（本地持久化）
│   └── chroma.sqlite3
├── app/
│   └── rag/
│       ├── embedder.py         # Embedding API 调用
│       ├── store.py            # Chroma 封装
│       ├── router.py           # 角色路由过滤
│       └── __init__.py
├── scripts/
│   └── populate_knowledge.py   # ← 你需要创建这个
└── souls/
    └── tool_config.yaml        # 各角色的工具白名单
```

## 常见问题

**Q: 检索返回空**
- 检查知识库是否有数据：`ChromaStore().collection.count()`
- 检查 `metadata.source` 是否与角色的允许列表匹配

**Q: 401 Unauthorized**
- 确认 `.env` 中 `EMBEDDINGS_API_KEY` 已设置且有效

**Q: 400 Bad Request**
- 检查 embedding API 的 `input` 格式，本系统要求 `string` 或 `string[]`