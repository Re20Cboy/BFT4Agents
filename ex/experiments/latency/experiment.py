"""
延迟实验主模块
"""

import sys
import os
import json
import time
import yaml
import re
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# 添加项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from ex.utils import import_helper, Plotter
from ex.experiments.latency.tracker import LatencyTracker
from ex.experiments.latency.consensus import BFT4AgentWithLatency


def expand_env_vars(config_value: Any) -> Any:
    """
    递归展开配置中的环境变量
    支持 ${VAR_NAME} 格式
    """
    if isinstance(config_value, str):
        # 匹配 ${VAR_NAME} 格式
        def replace_env_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(r'\$\{([^}]+)\}', replace_env_var, config_value)
    elif isinstance(config_value, dict):
        return {k: expand_env_vars(v) for k, v in config_value.items()}
    elif isinstance(config_value, list):
        return [expand_env_vars(item) for item in config_value]
    else:
        return config_value


class LatencyExperiment:
    """延迟实验类"""

    def __init__(self, config_file: str = None, output_dir: str = "ex/results"):
        self.config_file = config_file
        self.output_dir = output_dir

        # 创建输出目录
        os.makedirs(f"{output_dir}/data", exist_ok=True)
        os.makedirs(f"{output_dir}/figures", exist_ok=True)

        # 加载配置
        self.config = self._load_config()

        # 实验结果
        self.results = []

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # 默认配置
            return {
                'experiment_name': 'latency_test',
                'variables': {
                    'num_agents': [7],
                    'malicious_ratio': [0.14],
                    'network_delay': [[10, 100]],
                    'llm_backend': ['mock']
                },
                'tasks': {
                    'file': 'math_tasks_simple.json',
                    'num_tasks': 3,
                    'shuffle': False
                },
                'global': {
                    'timeout': 30.0,
                    'max_retries': 3,
                    'mock_accuracy': 1.0
                }
            }

    def run(self):
        """运行完整实验"""
        print(f"\n实验配置: {self.config['experiment_name']}")

        # 获取变量组合
        variables = self.config['variables']
        num_agents_list = variables.get('num_agents', [7])
        malicious_ratio_list = variables.get('malicious_ratio', [0.14])
        network_delay_list = variables.get('network_delay', [[10, 100]])
        llm_backend_list = variables.get('llm_backend', ['mock'])

        from itertools import product
        combinations = list(product(num_agents_list, malicious_ratio_list,
                                   network_delay_list, llm_backend_list))

        print(f"总共 {len(combinations)} 个实验配置\n")

        # 运行每个配置
        for i, (num_agents, mal_ratio, net_delay, llm_backend) in enumerate(combinations, 1):
            print(f"\n{'='*60}")
            print(f"配置 {i}/{len(combinations)}")
            print(f"  节点数: {num_agents}")
            print(f"  恶意比例: {mal_ratio:.2%}")
            print(f"  网络延迟: {net_delay}ms")
            print(f"  LLM后端: {llm_backend}")
            print(f"{'='*60}")

            result = self._run_single_config(num_agents, mal_ratio, net_delay, llm_backend)
            self.results.append(result)

        # 保存结果
        self._save_results()

    def _run_single_config(self, num_agents: int, malicious_ratio: float,
                          network_delay: tuple, llm_backend: str) -> Dict:
        """运行单个配置"""
        # 切换到bft4agent-simple目录（TaskLoader需要从data/tasks/加载）
        original_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        bft4agent_dir = os.path.join(project_root, 'bft4agent-simple')
        os.chdir(bft4agent_dir)

        try:
            # 创建LLM
            if llm_backend == "mock":
                llm = import_helper.LLMCaller(backend="mock", accuracy=self.config['global']['mock_accuracy'])
            else:
                # 从配置中获取LLM API配置
                llm_api_config = self.config.get('llm_api_config', {}).get(llm_backend, {})

                # 展开环境变量（如 ${QWEN_API_KEY} -> actual value）
                llm_api_config = expand_env_vars(llm_api_config)

                # 创建LLM，传递backend和API配置参数
                llm = import_helper.LLMCaller(backend=llm_backend, **llm_api_config)

            # 创建Agent
            agents = import_helper.create_agents(
                num_agents=num_agents,
                malicious_ratio=malicious_ratio,
                llm_caller=llm,
                role_configs=[],
                random_assignment=True
            )

            # 创建网络
            network = import_helper.Network(delay_range=network_delay, packet_loss=0.01)
            for agent in agents:
                network.register(agent)

            # 创建BFT
            bft = BFT4AgentWithLatency(
                agents=agents,
                network=network,
                timeout=self.config['global']['timeout'],
                max_retries=self.config['global']['max_retries']
            )

            # 加载任务
            num_tasks = self.config['tasks']['num_tasks']
            all_tasks = import_helper.TaskLoader({'tasks': self.config['tasks']}).load()

            # 运行任务
            task_results = []
            for i, task in enumerate(all_tasks[:num_tasks], 1):
                print(f"\n  任务 {i}/{num_tasks}: {task['content']}")
                result = bft.run(task)
                task_results.append(result)
                time.sleep(0.1)

            # 统计
            success_count = sum(1 for r in task_results if r['success'])

            print(f"\n  结果: {success_count}/{len(task_results)} 成功")

            return {
                'config': {
                    'num_agents': num_agents,
                    'malicious_ratio': malicious_ratio,
                    'network_delay': network_delay,
                    'llm_backend': llm_backend
                },
                'task_results': task_results,
                'summary': {
                    'total_tasks': len(task_results),
                    'success_count': success_count,
                    'success_rate': success_count / len(task_results)
                }
            }

        finally:
            # 恢复工作目录
            os.chdir(original_dir)

    def _generate_filename(self, timestamp: str) -> str:
        """生成包含实验信息的文件名"""
        # 提取配置信息
        exp_name = self.config.get('experiment_name', 'test')

        # 获取变量信息（如果是单值则显示，多值则显示range）
        variables = self.config.get('variables', {})
        num_agents = variables.get('num_agents', [7])
        malicious_ratios = variables.get('malicious_ratio', [0.14])

        # 构建描述性文件名
        parts = [exp_name]

        # 节点数信息
        if len(num_agents) == 1:
            parts.append(f"{num_agents[0]}agents")
        else:
            parts.append(f"{min(num_agents)}-{max(num_agents)}agents")

        # 恶意比例信息
        if len(malicious_ratios) == 1:
            parts.append(f"{int(malicious_ratios[0]*100)}malicious")
        else:
            parts.append(f"{int(min(malicious_ratios)*100)}-{int(max(malicious_ratios)*100)}malicious")

        # 添加时间戳
        parts.append(timestamp)

        return "_".join(parts)

    def _save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成描述性文件名
        filename = self._generate_filename(timestamp)
        output_file = f"{self.output_dir}/data/{filename}.json"

        data = {
            'experiment_name': self.config['experiment_name'],
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'results': self.results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n结果已保存: {output_file}")

        # 也保存为latest
        latest_file = f"{self.output_dir}/data/experiment_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_file

    def run_quick_test(self):
        """运行快速测试"""
        print("\n快速测试模式")
        print("="*60)

        # 简化配置
        self.config = {
            'experiment_name': 'quick_test',
            'variables': {
                'num_agents': [7],
                'malicious_ratio': [0.14],
                'network_delay': [[10, 100]],
                'llm_backend': ['mock']
            },
            'tasks': {
                'file': 'math_tasks_simple.json',
                'num_tasks': 3,
                'shuffle': False
            },
            'global': {
                'timeout': 30.0,
                'max_retries': 3,
                'mock_accuracy': 1.0
            }
        }

        self.run()

    def analyze_results(self, result_file: str):
        """分析结果"""
        print(f"\n分析结果文件: {result_file}")

        # 加载结果
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取数据
        records = []
        for exp_result in data['results']:
            config = exp_result['config']
            for task_result in exp_result['task_results']:
                if task_result.get('success'):
                    latency = task_result.get('latency_data', {})
                    records.append({
                        'num_agents': config['num_agents'],
                        'malicious_ratio': config['malicious_ratio'],
                        'task_success': True,
                        'view_changes': task_result.get('view_changes', 0),
                        'total_latency': latency.get('total', 0),
                        'pre_prepare_latency': latency.get('pre_prepare', {}).get('latency', 0),
                        'prepare_latency': latency.get('prepare', {}).get('latency', 0),
                        'commit_latency': latency.get('commit', {}).get('latency', 0),
                        'prepare_y_count': latency.get('prepare', {}).get('y_count', 0),
                        'prepare_n_count': latency.get('prepare', {}).get('n_count', 0),
                    })

        import pandas as pd
        df = pd.DataFrame(records)

        # 打印统计
        print(f"\n统计结果:")
        print(f"  总任务数: {len(df)}")
        print(f"  平均延迟: {df['total_latency'].mean():.4f}秒")
        print(f"  PRE-PREPARE: {df['pre_prepare_latency'].mean():.4f}秒")
        print(f"  PREPARE: {df['prepare_latency'].mean():.4f}秒")
        print(f"  COMMIT: {df['commit_latency'].mean():.4f}秒")

        # 绘图
        print(f"\n生成图表...")
        plotter = Plotter(output_dir=f"{self.output_dir}/figures")
        plotter.plot_latency_summary(df)
        plotter.plot_latency_vs_agents(df)

        print(f"\n图表已保存到: {self.output_dir}/figures/")
