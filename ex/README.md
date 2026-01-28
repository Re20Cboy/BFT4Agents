# BFT4Agent 实验系统

## 快速开始

### 唯一入口

```bash
# 快速测试（3个任务）
python ex/main.py latency --quick-test

# 完整实验（使用配置文件）
python ex/main.py latency --config ex/configs/latency.yaml

# 分析已有结果
python ex/main.py latency --analyze ex/results/data/experiment_latest.json
```

### 配置文件入口

所有实验配置位于 `ex/configs/` 目录：

- `latency.yaml` - 延迟实验配置

## 目录结构

```
ex/
├── main.py                    # 【统一入口】
├── configs/                   # 【配置入口】
│   └── latency.yaml
├── experiments/               # 实验模块
│   ├── latency/              # 延迟实验
│   │   ├── tracker.py        # 延迟跟踪器
│   │   ├── consensus.py      # 增强共识协议
│   │   └── experiment.py     # 延迟实验主逻辑
│   ├── accuracy/             # 准确率实验（预留）
│   └── scalability/          # 可扩展性实验（预留）
├── utils/                    # 工具模块
│   ├── import_helper.py      # 导入辅助
│   └── plotter.py            # 绘图工具
└── results/                  # 结果输出
    ├── data/                 # JSON数据
    └── figures/              # 图表
```

## 实验配置

编辑 `ex/configs/latency.yaml`:

```yaml
experiment_name: "latency_experiment"

variables:
  num_agents: [4, 7, 10]       # 测试不同节点数
  malicious_ratio: [0.0, 0.14] # 测试不同恶意比例
  network_delay: [[10, 100]]   # 网络延迟范围(ms)
  llm_backend: ["mock"]        # LLM后端

tasks:
  file: "math_tasks_simple.json"
  num_tasks: 5                 # 每个配置运行的任务数

global:
  timeout: 30.0
  max_retries: 3
  mock_accuracy: 1.0
```

## 结果输出

### 数据文件
- `ex/results/data/experiment_YYYYMMDD_HHMMSS.json` - 时间戳命名
- `ex/results/data/experiment_latest.json` - 最新结果

### 图表文件
- `ex/results/figures/latency_summary.png` - 综合仪表板
- `ex/results/figures/latency_vs_agents.png` - 延迟vs节点数

## 延迟测量说明

由于代码使用同一个LLM后端顺次执行，延迟计算基于：

- **PREPARE阶段延迟** = 收集到2f+1个Y消息中最后一个的到达时间
- **COMMIT阶段延迟** = 收集到2f+1个COMMIT消息中最后一个的到达时间

模拟并行场景：每个消息的到达时间 = 发送时间 + 随机网络延迟
