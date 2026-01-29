# 恶意节点比例与延迟关系实验

## 实验概述

本实验旨在研究在基于BFT的多智能体系统中，**恶意节点比例**对系统性能（特别是延迟）的影响。通过固定节点规模和任务类型，系统地改变恶意节点数量，观察并记录系统延迟、成功率、视图切换次数等关键指标的变化趋势。

## 研究问题

1. **延迟与恶意比例的关系**：随着恶意节点比例的增加，系统的端到端延迟如何变化？
2. **成功率影响**：恶意节点增加时，系统达成共识的成功率是否会下降？
3. **视图切换频率**：恶意节点是否会导致更多的视图切换（view change）操作？
4. **各阶段延迟分析**：PREPARE和COMMIT阶段的延迟分别受到何种影响？

## 实验设计

### 固定参数

- **节点总数**：20个
- **任务类型**：数学问题（math_tasks_simple.json）
- **网络延迟**：[10, 100] ms（默认值）
- **LLM后端**：qwen
- **任务数量**：每个配置运行3个任务（随机选择）
- **超时时间**：30秒
- **最大重试次数**：15次（说明见下文）

### 变化参数

| 实验组 | 恶意节点数 | 恶意比例 | 满足BFT条件 |
|--------|-----------|---------|------------|
| 组1    | 1         | 5%      | ✅ (1/20 < 1/3) |
| 组2    | 2         | 10%     | ✅ (2/20 < 1/3) |
| 组3    | 3         | 15%     | ✅ (3/20 < 1/3) |
| 组4    | 4         | 20%     | ✅ (4/20 < 1/3) |
| 组5    | 5         | 25%     | ✅ (5/20 < 1/3) |
| 组6    | 6         | 30%     | ✅ (6/20 < 1/3) |

**注**：根据BFT理论，系统可容忍的最大恶意节点比例为1/3（约33.3%）。本实验测试的6%-30%均在安全范围内，但逐渐逼近阈值。

### 测量指标

每个实验配置将记录以下指标：

1. **总延迟（Total Latency）**
   - 从任务提交到最终结果输出的完整时间

2. **分阶段延迟**
   - PRE-PREPARE阶段延迟
   - PREPARE阶段延迟
   - COMMIT阶段延迟

3. **共识指标**
   - 成功率：成功达成共识的任务比例
   - 视图切换次数：因Leader失败或提案被拒导致的重新选举次数
   - 投票统计：PREPARE阶段的Y/N票数

4. **系统性能**
   - 消息总数
   - 实际执行时间

## 快速开始

### 1. 快速测试（使用Mock LLM）

```bash
# 运行快速测试（7个节点，1-2个恶意节点，3个任务）
python ex/main.py malicious_vs_latency --quick-test
```

### 2. 完整实验（使用Qwen API）

首先配置API密钥：

```bash
export QWEN_API_KEY="your_api_key_here"
export QWEN_APP_ID="your_app_id_here"
```

然后运行实验：

```bash
# 使用默认配置文件
python ex/main.py malicious_vs_latency

# 或指定配置文件
python ex/main.py malicious_vs_latency --config ex/configs/malicious_vs_latency.yaml
```

### 3. 分析已有结果

```bash
python ex/main.py malicious_vs_latency --analyze ex/results/data/experiment_latest.json
```

## 实验流程

```
开始
  ↓
加载配置文件
  ↓
对于每个恶意节点数（1-6）：
  ↓
  创建20个Agent（其中N个为恶意）
  ↓
  初始化网络和BFT协议
  ↓
  运行5个数学任务
  ↓
  记录每个任务的：
    - 延迟数据
    - 成功/失败状态
    - 视图切换次数
    - 投票统计
  ↓
保存结果到JSON文件
  ↓
生成可视化图表
  ↓
结束
```

## 结果输出

### 数据文件

实验结果保存在 `ex/results/data/` 目录：

- `malicious_vs_latency_experiment_YYYYMMDD_HHMMSS.json` - 带时间戳的结果文件
- `experiment_latest.json` - 最新实验结果的链接

JSON文件结构：

```json
{
  "experiment_name": "malicious_vs_latency_experiment",
  "description": "测试不同恶意节点比例对系统延迟的影响",
  "timestamp": "2025-01-29T12:34:56",
  "config": {
    "variables": {...},
    "tasks": {...},
    "global": {...}
  },
  "results": [
    {
      "config": {
        "num_agents": 20,
        "malicious_count": 1,
        "malicious_ratio": 0.05,
        ...
      },
      "task_results": [...],
      "summary": {
        "success_rate": 1.0,
        "avg_total_latency": 2.345,
        "avg_prepare_latency": 1.234,
        "avg_commit_latency": 0.567,
        "avg_view_changes": 0.0,
        ...
      }
    },
    ...
  ]
}
```

### 可视化图表

分析脚本会生成以下图表（保存在 `ex/results/figures/`）：

1. **malicious_vs_latency_summary.png** - 综合仪表板（2×2子图）
   - 总延迟 vs 恶意比例
   - 成功率 vs 恶意比例
   - 各阶段延迟对比（柱状图）
   - 视图切换次数 vs 恶意比例

2. **malicious_vs_latency_trend.png** - 延迟趋势聚焦图
   - 高亮显示总延迟随恶意比例变化的趋势
   - 包含数据标签和置信区间

## 预期结果分析

### 理论预期

根据BFT4Agent协议设计，预期观察到以下趋势：

1. **延迟逐渐增加**
   - 恶意节点可能发送冲突消息或延迟响应
   - 需要更多时间收集足够的投票（2f+1）

2. **视图切换增多**
   - 恶意Leader可能被检测并替换
   - 需要更多轮次才能达成共识

3. **成功率下降**
   - 当恶意比例接近30%时，失败率可能上升
   - 但在BFT阈值内（<33%），系统应仍能达成共识

4. **PREPARE阶段延迟增长**
   - 恶意节点倾向于投N票或延迟投票
   - 影响法定人数达成速度

### 结果解读建议

- **延迟激增点**：识别延迟开始显著增长的恶意比例阈值
- **成功率拐点**：找到成功率明显下降的临界点
- **视图切换峰值**：分析哪些恶意比例最不稳定
- **与理论对比**：将实际结果与BFT理论预期进行对比

## 配置说明

### 为什么每个配置只运行3个任务？

为了平衡实验效率和统计可靠性，每个配置只运行3个随机选择的任务。原因：

1. **效率考虑**：6个配置 × 3个任务 = 18个总任务，每个任务可能需要多次视图切换
2. **统计充足**：3个任务足以观察趋势，同时避免过长的实验时间
3. **随机性**：每次实验会从任务池中随机选择，避免固定任务集的偏差

### 为什么max_retries设置为15？

原默认值为3，但在高恶意比例环境下不合适：

1. **恶意Leader概率**：当恶意比例为30%（6/20）时，连续遇到恶意Leader的概率显著增加
2. **需要更多尝试**：系统可能需要多次视图切换才能找到诚实Leader
3. **避免过早失败**：15次尝试足以在大多数情况下达成共识，同时避免无限循环
4. **符合实际情况**：真实恶意场景下，共识过程确实需要更多轮次

## 扩展实验

在完成基础实验后，可考虑以下扩展：

1. **增加任务数量**：如果需要更精确的统计，可以将num_tasks增加到5-10个
2. **节点规模变化**
   - 测试不同节点数（10, 30, 50）下的影响
   - 观察规模效应是否改变趋势

2. **网络延迟影响**
   - 测试不同网络延迟范围
   - 研究网络条件与恶意行为的交互效应

3. **攻击策略变化**
   - 测试不同类型的恶意行为（静默、随机投票、协调攻击）
   - 分析系统对不同攻击模式的鲁棒性

4. **LLM后端对比**
   - 使用不同LLM（GPT-4, Claude, DeepSeek）
   - 研究模型能力对系统抗干扰性的影响

## 故障排查

### 常见问题

**Q: 实验运行缓慢**
- A: 使用真实LLM API时，每个任务可能需要几秒到几十秒。建议先用`--quick-test`验证流程。

**Q: 成功率为0**
- A: 检查API密钥配置是否正确，或LLM服务是否可用。先用mock模式测试。

**Q: 恶意节点比例过高导致失败**
- A: 确保恶意比例不超过33%（20节点中最多6个恶意节点）。

**Q: 图表显示乱码**
- A: 确保系统安装了中文字体（如SimHei）。在Linux上可能需要：`sudo apt-get install fonts-wqy-zenhei`

## 技术细节

### 代码结构

```
ex/experiments/malicious_vs_latency/
├── __init__.py           # 模块初始化
├── experiment.py         # 实验主逻辑
└── README.md            # 本文档
```

### 关键类和方法

- **MaliciousVsLatencyExperiment**：实验主类
  - `run()` - 运行完整实验
  - `_run_single_config()` - 运行单个配置
  - `analyze_results()` - 分析并可视化结果
  - `_plot_malicious_vs_latency()` - 绘制性能图表

### 依赖关系

本实验复用了以下模块：

- `ex.experiments.latency.consensus.BFT4AgentWithLatency` - 带延迟测量的BFT协议
- `ex.experiments.latency.tracker.LatencyTracker` - 延迟跟踪器
- `ex.utils.import_helper` - 导入辅助工具
- `ex.utils.Plotter` - 绘图工具

## 参考文献

1. Castro, M., & Liskov, B. (1999). Practical Byzantine Fault Tolerance. OSDI.
2. paper.md - BFT4Agent协议设计文档
3. latency实验 - 端到端延迟测试实验

## 版本历史

- **v1.0** (2025-01-29)
  - 初始版本
  - 支持恶意节点比例1-6的测试
  - 完整的延迟和成功率分析
  - 可视化图表生成

---

**作者**：Claude Code
**最后更新**：2025-01-29
