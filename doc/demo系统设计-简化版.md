# BFT4Agent Demo 简化系统设计

## 📌 设计原则

**核心目标**: 实现可运行的BFT4Agent原型，用于论文实验验证

**简化策略**:
- ✅ 能模拟就用模拟（区块链、签名、VRF）
- ✅ 去掉过度抽象（复杂的配置系统、类型验证）
- ✅ 专注核心流程（BFT共识 + LLM验证）
- ✅ 快速上手（单个Python文件即可运行）

---

## 🎯 核心功能（最小集）

### 必须实现
1. **多Agent协同**: 模拟多个节点协作
2. **BFT共识**: 三阶段共识流程（提案→验证→提交）
3. **LLM调用**: 调用LLM进行推理和验证
4. **恶意节点模拟**: 模拟不同攻击行为
5. **数据收集**: 记录关键指标（延迟、准确率等）

### 暂不实现
- ❌ 真实P2P网络（单机多进程模拟）
- ❌ 真实区块链（用字典存储）
- ❌ 完整密码学签名（用简化HMAC）
- ❌ 复杂配置系统（用Python dict）
- ❌ 分布式部署（单机运行）

---

## 🏗️ 极简架构（3层）

```
┌─────────────────────────────────────┐
│   实验运行器 (Experiment Runner)    │  ← 运行实验，收集数据
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      BFT4Agent 共识核心              │  ← 提案→验证→提交
│  ┌─────────┐    ┌──────────┐        │
│  │ Leader  │    │ Backup   │        │
│  │ (推理)  │    │ (验证)   │        │
│  └─────────┘    └──────────┘        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        基础组件 (Utils)              │  ← LLM、网络、数据
│  • LLM Caller  • Network Simulator  │
│  • Data Logger  • Simple Storage    │
└─────────────────────────────────────┘
```

---

## 📦 核心模块（仅7个文件）

### 1. `agents.py` - Agent节点
```python
class Agent:
    """单个Agent节点（Leader + Backup）"""
    - 接收任务
    - 生成推理（Leader）
    - 验证提案（Backup）
    - 投票（Y/N）
```

### 2. `consensus.py` - 共识协议
```python
class BFT4Agent:
    """BFT4Agent共识流程"""
    - 选举Leader
    - 收集投票
    - 触发视图切换
    - 返回结果
```

### 3. `llm.py` - LLM接口
```python
class LLMCaller:
    """统一的LLM调用接口"""
    - Mock LLM（规则引擎）
    - OpenAI API
    - 验证提案
```

### 4. `network.py` - 网络模拟
```python
class Network:
    """简化的P2P网络模拟"""
    - 广播消息
    - 模拟延迟
    - 模拟丢包
```

### 5. `malicious.py` - 恶意行为
```python
class MaliciousBehavior:
    """恶意节点行为模拟"""
    - 懒惰Leader
    - 幻觉输出
    - 随机投票
```

### 6. `experiment.py` - 实验框架
```python
class Experiment:
    """运行实验，收集数据"""
    - 批量任务
    - 收集指标
    - 导出CSV
```

### 7. `main.py` - 主入口
```python
def main():
    """快速启动Demo"""
    # 创建7个Agent
    # 提交任务
    # 运行共识
    # 打印结果
```

---

## 🔧 配置简化

### 从复杂配置 → 简单字典

**之前**: 6个配置类，几十个参数
**现在**: 1个字典

```python
# config.py
CONFIG = {
    "num_agents": 7,
    "malicious_ratio": 0.14,
    "llm_backend": "mock",  # mock | openai
    "network_delay": (10, 100),  # ms
    "timeout": 30,  # seconds
}
```

---

## 📊 数据结构简化

### Message: 从复杂类 → 简单dict

```python
# 之前
msg = Message(msg_type=MessageType.PROPOSE, sender_id="...", ...)

# 现在
msg = {
    "type": "PROPOSE",
    "from": "agent_1",
    "to": "all",
    "data": {...},
    "time": time.time()
}
```

### Proposal: 从多类嵌套 → 简单dict

```python
proposal = {
    "task_id": "task_001",
    "leader_id": "agent_1",
    "reasoning": ["步骤1", "步骤2", "答案"],
    "answer": "42"
}
```

---

## 🧪 实验简化

### 测试指标（核心5个）

1. **端到端延迟**: `result["end_time"] - result["start_time"]`
2. **共识成功率**: `success_count / total_count`
3. **任务准确率**: 与ground_truth对比
4. **视图切换次数**: `result["view_changes"]`
5. **恶意节点容忍度**: 不同恶意比例下的成功率

### 测试流程

```python
# 1. 创建实验
exp = Experiment(
    num_agents=7,
    malicious_ratio=0.14,
    tasks=load_tasks("math_tasks.json")
)

# 2. 运行
results = exp.run()

# 3. 分析
print(f"准确率: {results['accuracy']:.2%}")
print(f"平均延迟: {results['avg_latency']:.2f}s")

# 4. 导出
results.to_csv("experiment_results.csv")
```

---

## 📁 简化后的目录结构

```
bft4agent-simple/
├── README.md              # 快速开始指南
├── requirements.txt       # 仅3个依赖
├── config.py             # 简单配置（1个dict）
├── agents.py             # Agent节点
├── consensus.py          # BFT共识
├── llm.py                # LLM接口
├── network.py            # 网络模拟
├── malicious.py          # 恶意行为
├── experiment.py         # 实验框架
├── main.py               # 主入口
├── run_tests.py          # 快速测试
├── data/
│   ├── tasks/            # 测试任务
│   │   └── math_tasks.json
│   └── results/          # 实验结果
└── notebooks/
    └── analysis.ipynb    # 数据分析
```

**对比之前**: 从20+文件 → 精简到10个核心文件

---

## 🚀 快速开始（3步）

### Step 1: 安装依赖
```bash
pip install pyyaml openai  # 仅2个核心依赖
```

### Step 2: 运行Demo
```python
python main.py
```

输出:
```
=== BFT4Agent Demo ===
Agents: 7 (1 malicious)
Task: 计算 23 * 47 = ?

[Agent_1] Leader: 推理中...
[Agent_2-7] Backups: 验证中...
投票: YYYYYYN  (6/7 通过)

✅ 共识成功!
答案: 1081
用时: 2.3s
视图切换: 0次
```

### Step 3: 运行实验
```python
python experiment.py --config my_config.yaml
```

---

## 📝 核心代码示例

### 完整共识流程（简化版）

```python
async def run_consensus(task, agents):
    """运行一次共识"""

    # 1. 选举Leader
    leader = random.choice(agents)
    backup_agents = [a for a in agents if a != leader]

    # 2. Leader生成提案
    proposal = leader.propose(task)
    network.broadcast(proposal, to=backup_agents)

    # 3. Backups验证并投票
    votes = {}
    for agent in backup_agents:
        vote = agent.validate(proposal)
        votes[agent.id] = vote  # "Y" or "N"

    # 4. 统计投票
    yes_count = sum(1 for v in votes.values() if v == "Y")

    # 5. 决策
    if yes_count > len(agents) * 2/3:
        return {"success": True, "answer": proposal["answer"]}
    else:
        return {"success": False, "reason": "Not enough votes"}
```

**只需30行代码！**

---

## 🎯 实现优先级

### Phase 1: 最小可用版本 (1周)
- [ ] 基础数据结构（dict）
- [ ] Agent节点（Leader + Backup）
- [ ] 简单LLM（Mock）
- [ ] 基础共识流程

### Phase 2: 完善功能 (1周)
- [ ] 恶意节点行为
- [ ] 视图切换
- [ ] 延迟模拟
- [ ] 数据收集

### Phase 3: 实验框架 (1周)
- [ ] 批量任务
- [ ] 指标统计
- [ ] 结果导出
- [ ] 简单可视化

**总计**: 3周完成可用的Demo系统

---

## 💡 与原设计对比

| 方面 | 原设计 | 简化设计 |
|------|--------|----------|
| 文件数 | 20+ | 10 |
| 配置类 | 6个 | 0个（用dict） |
| 数据类 | 10+ | 0个（用dict） |
| 验证层 | 复杂 | 无 |
| 依赖 | 30+ | 2-3个 |
| 学习曲线 | 陡峭 | 平缓 |
| 适用场景 | 生产级 | 快速实验 |

---

## 📊 预期效果

### 代码量
- **原设计**: ~2000行
- **简化设计**: ~800行（减少60%）

### 开发时间
- **原设计**: 10周
- **简化设计**: 3周（减少70%）

### 上手难度
- **原设计**: 需要深入理解架构
- **简化设计**: 30分钟看懂核心逻辑

---

## ✅ 验收标准

系统能够：
1. ✅ 运行完整的BFT4Agent共识流程
2. ✅ 测试不同恶意节点比例的影响
3. ✅ 记录端到端延迟
4. ✅ 计算任务准确率
5. ✅ 导出CSV格式的实验数据

满足论文实验章节的所有测试需求！

---

**文档版本**: v2.0 (简化版)
**最后更新**: 2025-01-20
**状态**: ✅ 准备实施