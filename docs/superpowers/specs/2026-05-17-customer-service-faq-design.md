# 客服 FAQ 快速匹配设计方案

## 背景与目标

客户需求中"客服Agent"明确要求：常见问题（如申请流程、学费标准、退费政策等高频问题）"秒级回复"，提升准确率。

当前 `knowledge_search` 依赖 ChromaDB 向量检索 + LLM 生成，FAQ 场景没有优先级通道，响应不够稳定。

本方案为 guest 角色（客服Agent）提供 FAQ 快速匹配通道：命中预建索引时返回标准答案给 LLM 包装，未命中时正常走 RAG。

---

## 架构概览

```
knowledge_search(query, top_k=5)
  │
  ├─► FAQ 匹配（仅 faq_roles 配置中的角色）
  │       ├─ BM25 快速检索 processed/faq.md 的 53 条 Q&A
  │       ├─ top-1 与 top-2 分数差 > 5 → 取 answer 作为 context
  │       └─ 差 ≤ 5 → fallback RAG
  │
  └─► RAG 向量检索（Chromadb）
          └─ 结果返回 LLM
```

LLM 感知不到 FAQ 通道的存在，收到的是增强后的 context。

---

## FAQ 数据格式

源文件：`knowledge/processed/company/public/faq.md`

格式（每条 FAQ）：
```markdown
## 问题标题
答案内容段落
```

解析方式：正则按 `## ` 分割，取第一行作为 question，去除 `##` 前缀后存入 BM25 索引。

示例：
```markdown
## 公司简称什么？
简称"粤教服务"。
```

→ `question = "公司简称什么？"`, `answer = "简称\"粤教服务\"。"`

---

## 配置机制

**配置文件**：`souls/tool_config.yaml` 新增 `faq_roles` 字段

```yaml
faq_roles:
  - guest
```

`faq_roles` 为角色列表，当前仅 `"guest"`。

后续其他角色需要 FAQ 快速匹配时，在列表中添加角色名即可，无需修改代码。

---

## 角色判断逻辑

`knowledge_search` 内部：

```python
def knowledge_search(query: str, top_k: int = 5) -> str:
    router = rag_router.knowledge_router
    role = router.soul_manager.current_role
    use_faq = role in (router.faq_roles or [])

    if use_faq:
        # BM25 + fallback RAG
    else:
        # 直接 RAG
```

`soul_manager.current_role` 在 `chat.py` 的 `/chat` 请求处理中已被正确加载。

---

## BM25 算法

**算法选择**：rank_bm25（Python BM25 实现）

**索引构建时机**：应用启动时（`app/api/main.py` 的 startup_event）

**索引内容**：53 条 FAQ，每条包含 `question` 和 `answer`

**匹配逻辑**：
1. BM25 检索，返回 top-2 候选
2. 计算 top-1 分数 - top-2 分数 = score_diff
3. score_diff > 5 → 取 top-1 answer 作为 context
4. score_diff ≤ 5 → fallback RAG

阈值 5 为经验值，可通过配置调整。

**为什么不用绝对阈值**：相对差值能反映匹配"明显程度"，避免问法模糊时误触发。

---

## FAQ 命中的返回格式

命中时，将 answer 包装为与 RAG 结果一致的格式：

```python
answer = f"""【常见问题参考】
标准答案：{faq_answer}

请以客服助手人设，将上述信息自然地回复给用户。"""
```

LLM 收到后按 SOUL 的人设语气包装返回，实现"秒级标准答案 + 自然语气"。

未命中走正常 RAG 流程，完全不受影响。

---

## 文件改动清单

| 文件 | 改动 |
|------|------|
| `souls/tool_config.yaml` | 新增 `faq_roles: [guest]` |
| `app/api/main.py` | startup_event 中调用 `FaqIndex.build()` |
| `app/agent/tools/rag.py` | `knowledge_search` 加 FAQ 通道判断和 BM25 逻辑 |
| `app/rag/faq_index.py`（新建） | BM25 索引封装，含 build() / search() / parse_faq() |
| `app/rag/router.py` | `KnowledgeRouter` 读取 `faq_roles` 配置 |

---

## 测试验证点

1. **FAQ 命中**：guest 问"公司简称什么"，BM25 差值 > 5，answer 直接给 LLM
2. **FAQ 未命中**：guest 问模糊问题，差值 ≤ 5，正常走 RAG
3. **非 FAQ 角色**：employee/student 完全绕过 BM25，直走 RAG
4. **配置扩展**：tool_config.yaml 加 `"employee"` 后，employee 也走 BM25

---

## 后续扩展

- 其他角色（如 employee）需要 FAQ 快速匹配时：
  1. 将对应 FAQ 内容加入 `knowledge/processed/company/internal/faq.md` 或新建文件
  2. `FaqIndex.build()` 时按角色加载对应 FAQ 文件
  3. `tool_config.yaml` 的 `faq_roles` 列表加入 `"employee"`