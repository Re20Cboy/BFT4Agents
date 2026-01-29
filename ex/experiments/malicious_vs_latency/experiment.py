"""
恶意节点比例与延迟关系实验主模块

研究目标：
- 在固定节点规模(20)下，测试不同恶意节点比例对系统性能的影响
- 分析恶意节点数量增加时，延迟、视图切换次数、成功率的变化趋势

实验设置：
- 固定：节点数20，数学问题，默认网络延迟[10,100]ms，qwen后端
- 变化：恶意节点数 1→6 (5%→30%)
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


class MaliciousVsLatencyExperiment:
    """恶意节点比例与延迟关系实验类"""

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
                'experiment_name': 'malicious_vs_latency_test',
                'variables': {
                    'num_agents': [20],
                    'malicious_count': [1, 2, 3, 4, 5, 6],
                    'network_delay': [[10, 100]],
                    'llm_backend': ['mock']
                },
                'tasks': {
                    'file': 'math_tasks_simple.json',
                    'num_tasks': 5,
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
        print(f"实验描述: {self.config.get('description', '')}")

        # 获取变量组合
        variables = self.config['variables']
        num_agents_list = variables.get('num_agents', [20])
        malicious_count_list = variables.get('malicious_count', [1, 2, 3])
        network_delay_list = variables.get('network_delay', [[10, 100]])
        llm_backend_list = variables.get('llm_backend', ['mock'])

        from itertools import product
        combinations = list(product(num_agents_list, malicious_count_list,
                                   network_delay_list, llm_backend_list))

        print(f"\n总共 {len(combinations)} 个实验配置")
        print(f"节点数: {num_agents_list}")
        print(f"恶意节点数: {malicious_count_list}")
        print(f"网络延迟: {network_delay_list}")
        print(f"LLM后端: {llm_backend_list}")

        # 运行每个配置
        for i, (num_agents, mal_count, net_delay, llm_backend) in enumerate(combinations, 1):
            malicious_ratio = mal_count / num_agents
            print(f"\n{'='*70}")
            print(f"配置 {i}/{len(combinations)}")
            print(f"  节点数: {num_agents}")
            print(f"  恶意节点数: {mal_count} ({malicious_ratio:.1%})")
            print(f"  网络延迟: {net_delay}ms")
            print(f"  LLM后端: {llm_backend}")
            print(f"{'='*70}")

            result = self._run_single_config(num_agents, malicious_ratio, net_delay, llm_backend, mal_count)
            self.results.append(result)

        # 保存结果
        self._save_results()

    def _run_single_config(self, num_agents: int, malicious_ratio: float,
                          network_delay: tuple, llm_backend: str,
                          malicious_count: int) -> Dict:
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

            # 计算平均延迟
            successful_results = [r for r in task_results if r['success']]
            if successful_results:
                avg_total_latency = sum(r['latency_data']['total'] for r in successful_results) / len(successful_results)
                avg_prepare_latency = sum(r['latency_data']['prepare']['latency'] for r in successful_results) / len(successful_results)
                avg_commit_latency = sum(r['latency_data']['commit']['latency'] for r in successful_results) / len(successful_results)
                avg_view_changes = sum(r['view_changes'] for r in successful_results) / len(successful_results)

                # 投票统计
                avg_prepare_y = sum(r['latency_data']['prepare']['y_count'] for r in successful_results) / len(successful_results)
                avg_prepare_n = sum(r['latency_data']['prepare']['n_count'] for r in successful_results) / len(successful_results)
            else:
                avg_total_latency = 0
                avg_prepare_latency = 0
                avg_commit_latency = 0
                avg_view_changes = 0
                avg_prepare_y = 0
                avg_prepare_n = 0

            print(f"\n  结果: {success_count}/{len(task_results)} 成功")
            print(f"  平均总延迟: {avg_total_latency:.3f}秒")
            print(f"  平均PREPARE延迟: {avg_prepare_latency:.3f}秒")
            print(f"  平均COMMIT延迟: {avg_commit_latency:.3f}秒")
            print(f"  平均视图切换: {avg_view_changes:.1f}次")

            return {
                'config': {
                    'num_agents': num_agents,
                    'malicious_count': malicious_count,
                    'malicious_ratio': malicious_ratio,
                    'network_delay': network_delay,
                    'llm_backend': llm_backend
                },
                'task_results': task_results,
                'summary': {
                    'total_tasks': len(task_results),
                    'success_count': success_count,
                    'success_rate': success_count / len(task_results) if len(task_results) > 0 else 0,
                    'avg_total_latency': avg_total_latency,
                    'avg_prepare_latency': avg_prepare_latency,
                    'avg_commit_latency': avg_commit_latency,
                    'avg_view_changes': avg_view_changes,
                    'avg_prepare_y_count': avg_prepare_y,
                    'avg_prepare_n_count': avg_prepare_n,
                }
            }

        finally:
            # 恢复工作目录
            os.chdir(original_dir)

    def _generate_filename(self, timestamp: str) -> str:
        """生成包含实验信息的文件名"""
        exp_name = self.config.get('experiment_name', 'test')
        return f"{exp_name}_{timestamp}"

    def _save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self._generate_filename(timestamp)
        output_file = f"{self.output_dir}/data/{filename}.json"

        data = {
            'experiment_name': self.config['experiment_name'],
            'description': self.config.get('description', ''),
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
            'experiment_name': 'malicious_vs_latency_quick_test',
            'description': '快速测试恶意节点比例与延迟关系',
            'variables': {
                'num_agents': [7],
                'malicious_count': [1, 2],
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
            summary = exp_result['summary']

            records.append({
                'malicious_count': config['malicious_count'],
                'malicious_ratio': config['malicious_ratio'],
                'num_agents': config['num_agents'],
                'success_rate': summary['success_rate'],
                'avg_total_latency': summary['avg_total_latency'],
                'avg_prepare_latency': summary['avg_prepare_latency'],
                'avg_commit_latency': summary['avg_commit_latency'],
                'avg_view_changes': summary['avg_view_changes'],
                'avg_prepare_y_count': summary['avg_prepare_y_count'],
                'avg_prepare_n_count': summary['avg_prepare_n_count'],
            })

        # 按恶意节点数排序
        records.sort(key=lambda x: x['malicious_count'])

        # 打印统计结果
        print(f"\n{'='*70}")
        print(f"实验结果汇总")
        print(f"{'='*70}")
        print(f"{'恶意节点数':<10} {'恶意比例':<12} {'成功率':<10} {'总延迟(s)':<12} {'视图切换':<10}")
        print(f"{'-'*70}")

        for r in records:
            print(f"{r['malicious_count']:<10} {r['malicious_ratio']:>10.1%} "
                  f"{r['success_rate']:>8.1%} {r['avg_total_latency']:>10.3f} {r['avg_view_changes']:>8.1f}")

        print(f"{'='*70}\n")

        # 绘图
        print(f"\n生成图表...")
        plotter = Plotter(output_dir=f"{self.output_dir}/figures")
        self._plot_malicious_vs_latency(records, plotter)

        print(f"\n图表已保存到: {self.output_dir}/figures/")

    def _plot_malicious_vs_latency(self, records: List[Dict], plotter: Plotter):
        """绘制恶意节点比例与延迟关系图"""
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

        malicious_ratios = [r['malicious_ratio'] for r in records]
        malicious_counts = [r['malicious_count'] for r in records]

        # 创建多子图
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('恶意节点比例与系统性能关系', fontsize=16, fontweight='bold')

        # 图1: 总延迟 vs 恶意比例
        ax1 = axes[0, 0]
        ax1.plot(malicious_ratios, [r['avg_total_latency'] for r in records],
                marker='o', linewidth=2, markersize=8, color='#2E86AB', label='总延迟')
        ax1.set_xlabel('恶意节点比例', fontsize=12)
        ax1.set_ylabel('平均总延迟 (秒)', fontsize=12)
        ax1.set_title('总延迟 vs 恶意节点比例', fontsize=13)
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 添加X轴标签显示具体节点数
        ax1.set_xticks(malicious_ratios)
        ax1.set_xticklabels([f'{int(r*100)}%\n({c}节点)'
                            for r, c in zip(malicious_ratios, malicious_counts)], fontsize=9)

        # 图2: 成功率 vs 恶意比例
        ax2 = axes[0, 1]
        ax2.plot(malicious_ratios, [r['success_rate'] for r in records],
                marker='s', linewidth=2, markersize=8, color='#A23B72', label='成功率')
        ax2.axhline(y=2/3, color='r', linestyle='--', alpha=0.5, label='BFT阈值(66.7%)')
        ax2.set_xlabel('恶意节点比例', fontsize=12)
        ax2.set_ylabel('成功率', fontsize=12)
        ax2.set_title('成功率 vs 恶意节点比例', fontsize=13)
        ax2.set_ylim([0, 1.05])
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        ax2.set_xticks(malicious_ratios)
        ax2.set_xticklabels([f'{int(r*100)}%\n({c}节点)'
                            for r, c in zip(malicious_ratios, malicious_counts)], fontsize=9)

        # 图3: 各阶段延迟对比
        ax3 = axes[1, 0]
        x = range(len(malicious_ratios))
        width = 0.35
        ax3.bar([i - width/2 for i in x], [r['avg_prepare_latency'] for r in records],
               width, label='PREPARE延迟', color='#F18F01', alpha=0.8)
        ax3.bar([i + width/2 for i in x], [r['avg_commit_latency'] for r in records],
               width, label='COMMIT延迟', color='#C73E1D', alpha=0.8)
        ax3.set_xlabel('恶意节点数', fontsize=12)
        ax3.set_ylabel('平均延迟 (秒)', fontsize=12)
        ax3.set_title('各阶段延迟对比', fontsize=13)
        ax3.set_xticks(x)
        ax3.set_xticklabels([f'{c}\n({int(r*100)}%)'
                            for c, r in zip(malicious_counts, malicious_ratios)], fontsize=9)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        # 图4: 视图切换次数 vs 恶意比例
        ax4 = axes[1, 1]
        ax4.plot(malicious_ratios, [r['avg_view_changes'] for r in records],
                marker='^', linewidth=2, markersize=8, color='#3B1F2B', label='视图切换次数')
        ax4.set_xlabel('恶意节点比例', fontsize=12)
        ax4.set_ylabel('平均视图切换次数', fontsize=12)
        ax4.set_title('视图切换次数 vs 恶意节点比例', fontsize=13)
        ax4.grid(True, alpha=0.3)
        ax4.legend()

        ax4.set_xticks(malicious_ratios)
        ax4.set_xticklabels([f'{int(r*100)}%\n({c}节点)'
                            for r, c in zip(malicious_ratios, malicious_counts)], fontsize=9)

        plt.tight_layout()

        # 保存图表
        output_file = f"{plotter.output_dir}/malicious_vs_latency_summary.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  已保存: {output_file}")
        plt.close()

        # 创建单图聚焦延迟趋势
        fig2, ax = plt.subplots(figsize=(10, 6))
        ax.plot(malicious_ratios, [r['avg_total_latency'] for r in records],
               marker='o', linewidth=2.5, markersize=10, color='#2E86AB', label='总延迟')
        ax.fill_between(malicious_ratios,
                       [r['avg_total_latency'] * 0.9 for r in records],
                       [r['avg_total_latency'] * 1.1 for r in records],
                       alpha=0.2, color='#2E86AB')

        ax.set_xlabel('恶意节点比例', fontsize=14)
        ax.set_ylabel('平均总延迟 (秒)', fontsize=14)
        ax.set_title('恶意节点比例对总延迟的影响（20节点系统）', fontsize=15, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=12)

        ax.set_xticks(malicious_ratios)
        ax.set_xticklabels([f'{int(r*100)}%\n({c}个恶意节点)'
                           for r, c in zip(malicious_ratios, malicious_counts)], fontsize=11)

        # 添加数据标签
        for i, (r, ratio) in enumerate(zip(records, malicious_ratios)):
            ax.annotate(f'{r["avg_total_latency"]:.2f}s',
                       (ratio, r['avg_total_latency']),
                       textcoords="offset points",
                       xytext=(0, 10),
                       ha='center',
                       fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

        plt.tight_layout()
        output_file2 = f"{plotter.output_dir}/malicious_vs_latency_trend.png"
        plt.savefig(output_file2, dpi=300, bbox_inches='tight')
        print(f"  已保存: {output_file2}")
        plt.close()
