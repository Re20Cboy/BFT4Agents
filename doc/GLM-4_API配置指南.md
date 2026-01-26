# GLM-4 API 配置使用指南

本指南详细说明如何将BFT4Agent项目的模拟LLM替换为真实的GLM-4 API。

---

## 📋 前置准备

### 1. 获取智谱AI API Key

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 在控制台获取你的API Key
4. 确保账户有足够的调用额度

### 2. 安装依赖包

```bash
pip install zhipuai
```

---

## 🔧 配置步骤

### 方法一：直接修改 config.py（推荐用于快速测试）

1. 打开文件：[config.py](bft4agent-simple/config.py)

2. 修改以下配置项：

```python
CONFIG = {
    # 修改LLM后端为zhipu
    "llm_backend": "zhipu",  # 从 "mock" 改为 "zhipu"

    # 配置智谱API
    "llm_api_config": {
        "zhipu": {
            "api_key": "your-actual-api-key-here",  # 填入你的API Key
            "model": "glm-4",  # 可选：glm-4, glm-4-plus, glm-4-0520等
        },
    },

    # ... 其他配置保持不变
}
```

3. 保存文件

### 方法二：使用 YAML 配置文件（推荐用于生产环境）

1. 复制配置示例文件：
```bash
cp config.example.yaml config.yaml
```

2. 编辑 `config.yaml`：
```yaml
llm_backend: zhipu

llm_api_config:
  zhipu:
    api_key: "your-actual-api-key-here"  # 填入你的API Key
    model: "glm-4"
```

3. 保存文件

---

## 🚀 运行测试

### 运行主程序
```bash
cd bft4agent-simple
python main.py
```

### 预期输出
```
====================================================
  BFT4Agent Demo - 简化原型
====================================================

=== config ===
Agent数量: 7
maliciousnode比例: 14.0%
LLM后端: zhipu
networkdelay: (10, 100) ms
法定人数比例: 66.7%

[init] 创建LLM (zhipu)...
[init] 创建 7 个Agent (1 个malicious)...
```

---

## 🎯 GLM-4 模型选择

智谱AI提供多个GLM-4模型版本，你可以根据需求选择：

| 模型名称 | 特点 | 适用场景 |
|---------|------|---------|
| `glm-4` | 标准版本，平衡性能和成本 | 通用场景 |
| `glm-4-plus` | 增强版本，能力更强 | 复杂推理任务 |
| `glm-4-0520` | 特定版本 | 特定场景 |
| `glm-4-air` | 轻量版本，响应更快 | 快速响应场景 |
| `glm-4-flash` | 最快响应速度 | 实时性要求高 |

修改配置中的 `model` 参数即可切换模型：
```python
"model": "glm-4-plus"  # 使用增强版本
```

---

## 🔍 API调用示例

### generate() - 生成推理和答案

```python
from llm import ZhipuLLM

# 初始化
llm = ZhipuLLM(api_key="your-api-key", model="glm-4")

# 生成答案
question = "23 * 47 = ?"
reasoning, answer = llm.generate(question)

print(f"推理过程: {reasoning}")
print(f"答案: {answer}")
```

**输出示例：**
```
推理过程: ['步骤1: 这是一个乘法问题', '步骤2: 计算 23 * 47 = 1081', '步骤3: 得出answer 1081']
答案: 1081
```

### validate() - 验证提案

```python
proposal = {
    "task_id": "math_001",
    "reasoning": ["步骤1", "步骤2"],
    "answer": "1081",
    "confidence": 0.95
}

decision, confidence = llm.validate(proposal)
print(f"决策: {decision}, 置信度: {confidence}")
```

**输出示例：**
```
决策: Y, 置信度: 0.9
```

---

## 🛠️ 故障排查

### 问题1：ImportError: 请安装zhipuai包

**解决方案：**
```bash
pip install zhipuai
```

### 问题2：API调用失败

**可能原因：**
1. API Key 错误或未填写
2. 网络连接问题
3. API额度不足

**解决方案：**
```python
# 测试API连接
from llm import ZhipuLLM

llm = ZhipuLLM(api_key="your-api-key", model="glm-4")
is_healthy = llm.health_check()
print(f"API状态: {'正常' if is_healthy else '异常'}")
```

### 问题3：答案解析失败

**可能原因：**
- GLM-4返回格式与预期不符

**解决方案：**
- 当前代码已包含智能解析逻辑，会自动处理各种返回格式
- 如仍有问题，可以在 [llm.py:391-415](bft4agent-simple/llm.py#L391-L415) 中调整解析逻辑

---

## 📊 性能对比

### Mock LLM vs GLM-4

| 指标 | Mock LLM | GLM-4 |
|-----|---------|-------|
| 响应速度 | 0.1-0.5秒 | 1-3秒 |
| 准确率 | 可配置（默认85%） | >95% |
| 推理质量 | 简单模拟 | 真实推理 |
| 成本 | 免费 | 按API调用计费 |
| 网络要求 | 无 | 需要网络连接 |

---

## 💡 最佳实践

### 1. API Key 安全
- 不要将API Key直接提交到代码仓库
- 使用环境变量或配置文件管理API Key
- 示例：
```python
import os
api_key = os.getenv("ZHIPU_API_KEY")
```

### 2. 错误处理
项目已包含完善的错误处理机制：
- API调用失败会返回错误提示
- 验证失败会使用默认值
- 所有异常都会被捕获并打印日志

### 3. 成本控制
- 先用Mock LLM进行开发和测试
- 确认功能正常后再切换到真实API
- 控制实验规模，避免不必要的API调用

### 4. 模型选择建议
- 开发测试：使用Mock LLM
- 快速验证：使用 `glm-4-flash`
- 正式实验：使用 `glm-4` 或 `glm-4-plus`

---

## 📝 配置检查清单

使用GLM-4 API前，请确认：

- [ ] 已安装 zhipuai 包
- [ ] 已获取智谱AI API Key
- [ ] 已修改 config.py 或创建 config.yaml
- [ ] API Key 已正确填写
- [ ] 已选择合适的模型（glm-4, glm-4-plus等）
- [ ] API账户有足够额度
- [ ] 网络连接正常

---

## 🔄 从Mock切换到真实API

### 快速切换步骤

1. **使用Mock（当前配置）：**
```python
"llm_backend": "mock",
```

2. **切换到GLM-4：**
```python
"llm_backend": "zhipu",
"llm_api_config": {
    "zhipu": {
        "api_key": "your-api-key",
        "model": "glm-4"
    }
}
```

3. **切换回Mock（用于测试）：**
```python
"llm_backend": "mock",
"mock_accuracy": 0.85
```

---

## 📚 相关文档

- [快速使用指南](快速使用指南.md)
- [系统设计文档](demo系统设计-简化版.md)
- [实验设计文档](实验设计.md)

---

## 🆘 获取帮助

如有问题，请检查：
1. [llm.py](bft4agent-simple/llm.py) - LLM接口实现
2. [config.py](bft4agent-simple/config.py) - 配置说明
3. [main.py](bft4agent-simple/main.py) - 主程序入口

---

**文档版本：** v1.0
**最后更新：** 2025-01-22
**作者：** BFT4Agent项目组
