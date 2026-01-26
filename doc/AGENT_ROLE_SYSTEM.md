# Agent角色系统说明文档

## 概述

BFT4Agent系统现在支持通过**Prompt工程**给不同Agent分配不同的专业角色，所有Agent共享同一个LLM，但通过不同的system prompt实现角色差异化。

## 核心设计

### 1. 共享LLM架构

```
┌──────────────────────────────────────┐
│          单个LLM实例                   │
│   (如：千问、GPT、智谱等)              │
└──────────────┬───────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
   Agent 1           Agent 2
  (数学专家)        (逻辑分析师)
      │                 │
  system_prompt:   system_prompt:
  "你是一位数学...  "你是一位逻辑...
```

### 2. 角色类型

系统预定义了5种专业角色：

| 角色名称 | 专业领域 | 验证风格 | 特点 |
|---------|---------|---------|------|
| 数学专家 | math | strict | 精确计算，严格验证 |
| 逻辑分析师 | logic | balanced | 分析逻辑结构，平衡验证 |
| 验证专家 | verification | strict | 善于发现错误，严格验证 |
| 综合思考者 | general | balanced | 多角度思考，平衡验证 |
| 批判性思维者 | critical | strict | 质疑答案，严格验证 |

### 3. 角色分配方式

在 `config.py` 中配置：

```python
"assign_roles_randomly": True,  # True=随机分配，False=按顺序分配
```

- **随机分配**：每个Agent随机获得一个角色（可能重复）
- **顺序分配**：循环使用角色列表，确保角色多样性

## 配置示例

### config.py 配置

```python
CONFIG = {
    # Agent配置
    "num_agents": 5,  # Agent数量
    "malicious_ratio": 0.2,  # 恶意节点比例

    # Agent角色配置
    "agent_roles": [
        {
            "name": "数学专家",
            "specialty": "math",
            "system_prompt": "你是一位数学专家，擅长精确计算和数学推理。请认真分析问题，给出准确的计算过程和答案。",
            "validation_style": "strict"
        },
        # ... 其他角色
    ],
    "assign_roles_randomly": True,  # 随机分配角色
}
```

## 工作原理

### 1. 提案生成（Leader）

当某个Agent被选为Leader时：

```python
# 原始问题
question = "2 + 2 = ?"

# 根据Leader的角色构建prompt
prompt = f"{leader.system_prompt}\n\n问题: {question}"

# 调用LLM
reasoning, answer = llm.generate(prompt)
```

**示例**：
- 如果Leader是"数学专家"，会得到精确的计算过程
- 如果Leader是"综合思考者"，会得到更全面的解释

### 2. 提案验证（Backup）

当Backup Agent验证提案时：

```python
# 根据验证者的角色构建验证prompt
validation_instruction = f"\n\n请从{agent.role_config['name']}的角度进行验证。"

if agent.validation_style == "strict":
    validation_instruction += "请严格检查答案的准确性，任何不确定或可疑的地方都应该否定。"

# 修改proposal
proposal["task_id"] += validation_instruction

# 调用LLM验证
decision = llm.validate(proposal)
```

**示例**：
- "验证专家"（strict）：更容易投反对票
- "综合思考者"（balanced）：更倾向于平衡判断

### 3. 恶意Agent行为

恶意Agent也可以使用LLM，但会添加恶意prompt：

```python
# 恶意Agent的验证prompt
malicious_prompt = """
请以批判的眼光审视这个答案，倾向于找出其中的问题并给出否定意见。
即使答案看起来正确，也请考虑是否存在潜在问题。
"""
```

**策略**：
- 30%概率：完全随机投票
- 70%概率：使用恶意prompt让LLM倾向于否定

## 使用场景

### 场景1：数学问题

```python
task = {"content": "23 * 47 = ?", "type": "math"}

# 假设Leader是"数学专家"
# 会得到：详细的计算步骤和精确答案1081

# 验证时：
# - "数学专家"会严格验证计算过程
# - "逻辑分析师"会检查推理逻辑
# - "验证专家"会寻找可能的错误
```

### 场景2：逻辑推理

```python
task = {"content": "如果所有的A都是B，所有的B都是C，那么所有的A都是C吗？", "type": "logic"}

# 假设Leader是"逻辑分析师"
# 会得到：详细的三段论分析

# 验证时：
# - "逻辑分析师"会检查推理的有效性
# - "批判性思维者"会质疑前提假设
```

### 场景3：恶意Agent影响

```python
# 假设agent_1是恶意的"数学专家"
task = {"content": "2 + 2 = ?", "type": "math"}

# 作为Leader时：
# - 可能给出错误的答案（如"5"）

# 作为Backup时：
# - 即使正确答案，也倾向于否定
# - 使用恶意prompt影响LLM判断
```

## 优势

### 1. 资源高效
- ✅ 所有Agent共享同一个LLM实例
- ✅ 无需为每个Agent配置不同的LLM
- ✅ 降低API调用成本

### 2. 灵活配置
- ✅ 通过prompt快速调整Agent角色
- ✅ 可以轻松添加新的角色类型
- ✅ 支持动态角色分配

### 3. 更真实的模拟
- ✅ 不同专业背景的Agent
- ✅ 不同的验证风格
- ✅ 恶意Agent也可以利用LLM

### 4. 可扩展性
- ✅ 可以添加更多角色（文学、历史、物理等）
- ✅ 可以调整验证风格的比例
- ✅ 可以实现复杂的恶意策略

## 配置建议

### 小规模测试（3-5个Agent）

```python
"num_agents": 5,
"malicious_ratio": 0.2,
"agent_roles": [  # 选择5个不同角色
    {"name": "数学专家", ...},
    {"name": "逻辑分析师", ...},
    {"name": "验证专家", ...},
    {"name": "综合思考者", ...},
    {"name": "批判性思维者", ...},
],
"assign_roles_randomly": False,  # 每个agent一个不同角色
```

### 大规模实验（7-15个Agent）

```python
"num_agents": 15,
"malicious_ratio": 0.2,
"agent_roles": [  # 5个角色，重复使用
    {"name": "数学专家", ...},
    {"name": "逻辑分析师", ...},
    {"name": "验证专家", ...},
    {"name": "综合思考者", ...},
    {"name": "批判性思维者", ...},
],
"assign_roles_randomly": True,  # 随机分配，允许重复
```

### 恶意节点测试

```python
"malicious_ratio": 0.4,  # 40%恶意节点
# 恶意节点会使用LLM但添加恶意prompt
```

## 自定义角色

您可以轻松添加新的角色类型：

```python
"agent_roles": [
    # 现有角色...
    {
        "name": "物理专家",
        "specialty": "physics",
        "system_prompt": "你是一位物理学专家，擅长物理计算和物理概念分析。",
        "validation_style": "strict"
    },
    {
        "name": "文学评论家",
        "specialty": "literature",
        "system_prompt": "你是一位文学评论家，擅长文本分析和语言理解。",
        "validation_style": "lenient"
    },
]
```

## 输出示例

运行时会显示每个Agent的角色：

```
=== Agent列表 ===
  agent_1: 数学专家, rep=1.00
  agent_2: 逻辑分析师, rep=1.00
  agent_3: 验证专家, rep=1.00
  agent_4: 综合思考者, rep=1.00
  agent_5: 批判性思维者 [malicious], rep=1.00
```

在BFT过程中：

```
[View 1] Leader: agent_1 (数学专家)
[agent_1] 生成提案...
  推理过程:
    1. 作为数学专家，我需要精确计算2+2
    2. 根据基本算术规则，2+2=4
  答案: 4

[Backups] 验证提案...
  [agent_2 (逻辑分析师)] Vote: Y - 逻辑清晰，推理合理
  [agent_3 (验证专家)] Vote: Y - 计算准确，无误
  [agent_4 (综合思考者)] Vote: Y - 答案正确
  [agent_5 (批判性思维者-恶意)] Vote: N - 可能存在计算陷阱
```

## 总结

这个角色系统通过**Prompt工程**实现了：
1. ✅ 所有Agent共享同一个LLM
2. ✅ 通过system prompt实现角色差异化
3. ✅ 恶意Agent也可以利用LLM扮演恶意角色
4. ✅ 灵活的角色配置和分配
5. ✅ 更真实的多智能体协作模拟

---

**最后更新**: 2025-01-23
**版本**: v2.0
