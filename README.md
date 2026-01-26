# BFT4Agent - 简化原型

基于拜占庭容错（BFT）的多智能体协同共识系统简化Demo，用于解决开放P2P环境下异构LLM智能体的可信共识问题。

## 快速开始

### 1. 安装依赖

```bash
pip install pyyaml pandas matplotlib
```

### 2. 配置API密钥（可选）

如需使用真实LLM，创建 `.env` 文件（参考 `.env.example`）：

```bash
# OpenAI
OPENAI_API_KEY=your_key_here

# 智谱AI
ZHIPU_API_KEY=your_key_here

# 阿里云千问
DASHSCOPE_API_KEY=your_key_here
QWEN_APP_ID=your_app_id_here
```

### 3. 运行Demo

```bash
cd bft4agent-simple
python main.py
```

## 项目结构

```
bft4agent-simple/
├── agents.py           # Agent节点实现
├── consensus.py        # BFT共识协议
├── llm_new.py          # LLM接口
├── llm_modules/        # LLM后端实现
│   ├── mock.py         # Mock模拟器
│   ├── openai.py       # OpenAI接口
│   ├── zhipu.py        # 智谱AI接口
│   └── qwen.py         # 千问接口
├── network.py          # 网络模拟
├── config.py           # 配置系统
└── main.py             # 主入口
```

## 核心功能

- **多智能体协同**：支持多个异构LLM智能体协同工作
- **拜占庭容错**：容忍部分恶意节点的攻击
- **角色分配**：支持不同专业领域的智能体角色
- **共识协议**：完整的提案→验证→投票流程
- **LLM后端**：支持Mock、OpenAI、智谱、千问等多种后端

## 配置说明

编辑 `bft4agent-simple/config.py`：

```python
CONFIG = {
    "num_agents": 5,              # Agent数量
    "malicious_ratio": 0.2,       # 恶意节点比例
    "llm_backend": "mock",        # LLM后端
    "network_delay": (10, 100),   # 网络延迟(ms)
    "timeout": 5.0,               # 超时时间(秒)
}
```

## 运行实验

### 切换LLM后端

```python
# 使用Mock（默认）
CONFIG["llm_backend"] = "mock"

# 使用OpenAI
CONFIG["llm_backend"] = "openai"

# 使用智谱AI
CONFIG["llm_backend"] = "zhipu"

# 使用千问
CONFIG["llm_backend"] = "qwen"
```

### 调整恶意节点比例

```python
# 0% 恶意节点
CONFIG["malicious_ratio"] = 0.0

# 20% 恶意节点
CONFIG["malicious_ratio"] = 0.2

# 33% 恶意节点（接近容忍上限）
CONFIG["malicious_ratio"] = 0.33
```

## 系统要求

- Python 3.9+
- 依赖包：pyyaml, pandas, matplotlib

## 许可证

MIT License
