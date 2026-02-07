"""
容错边界测试实验

实验目标：
1. 测试BFT4Agent协议的容错边界（理论上f/n ≤ 1/3）
2. 使用刁钻问题诱导诚实agent也产生错误
3. 分别测试leader为诚实和恶意两种场景
4. 使用真实LLM作为后端

关键假设：
- 即使诚实的LLM agent也可能因为幻觉、理解偏差而投错票
- 测试系统能否在"诚实agent出错 + 恶意agent攻击"的双重压力下达成共识
"""

import sys
import os
import json
import time
import yaml
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

# 添加项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from ex.utils import import_helper, Plotter
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


class FaultToleranceExperiment:
    """容错边界测试实验类"""

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
                'experiment_name': 'fault_tolerance_boundary_test',
                'description': '测试BFT4Agent协议在面对刁钻问题时的容错边界',
                'variables': {
                    'num_agents': [9],  # 固定9个节点（满足3f+1）
                    'malicious_count': [0, 1, 2, 3],  # 0%, 11%, 22%, 33%
                    'leader_type': ['honest', 'malicious'],  # 测试两种leader
                    'network_delay': [[10, 100]],
                    'llm_backend': ['qwen']  # 使用真实LLM
                },
                'tasks': {
                    'file': 'tricky_questions.json',  # 专门的刁钻问题数据集
                    'num_tasks': 5,
                    'shuffle': True
                },
                'global': {
                    'timeout': 60.0,  # 真实LLM需要更长超时
                    'max_retries': 10,  # 允许更多重试
                }
            }

    def run(self):
        """运行完整实验"""
        print(f"\n{'='*80}")
        print(f"容错边界测试实验")
        print(f"实验名称: {self.config['experiment_name']}")
        print(f"实验描述: {self.config.get('description', '')}")
        print(f"{'='*80}\n")

        # 获取变量组合
        variables = self.config['variables']
        num_agents_list = variables.get('num_agents', [9])
        malicious_count_list = variables.get('malicious_count', [0, 1, 2, 3])
        leader_type_list = variables.get('leader_type', ['honest', 'malicious'])
        network_delay_list = variables.get('network_delay', [[10, 100]])
        llm_backend_list = variables.get('llm_backend', ['qwen'])

        from itertools import product
        combinations = list(product(
            num_agents_list, malicious_count_list, leader_type_list,
            network_delay_list, llm_backend_list
        ))

        print(f"总共 {len(combinations)} 个实验配置\n")

        # 运行每个配置
        for i, (num_agents, mal_count, leader_type, net_delay, llm_backend) in enumerate(combinations, 1):
            malicious_ratio = mal_count / num_agents
            print(f"\n{'='*80}")
            print(f"配置 {i}/{len(combinations)}")
            print(f"  节点数: {num_agents}")
            print(f"  恶意节点数: {mal_count} ({malicious_ratio:.1%})")
            print(f"  Leader类型: {leader_type}")
            print(f"  网络延迟: {net_delay}ms")
            print(f"  LLM后端: {llm_backend}")
            print(f"{'='*80}")

            result = self._run_single_config(
                num_agents, malicious_ratio, net_delay, llm_backend,
                mal_count, leader_type
            )
            self.results.append(result)

        # 保存结果并分析
        output_file = self._save_results()
        self._analyze_results(output_file)

    def _run_single_config(
        self, num_agents: int, malicious_ratio: float,
        network_delay: tuple, llm_backend: str,
        malicious_count: int, leader_type: str
    ) -> Dict:
        """运行单个配置"""
        # 切换到bft4agent-simple目录
        original_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        bft4agent_dir = os.path.join(project_root, 'bft4agent-simple')
        os.chdir(bft4agent_dir)

        try:
            # 创建LLM
            if llm_backend == "mock":
                llm = import_helper.LLMCaller(
                    backend="mock",
                    accuracy=self.config['global'].get('mock_accuracy', 0.8)
                )
            else:
                llm_api_config = self.config.get('llm_api_config', {}).get(llm_backend, {})
                llm_api_config = expand_env_vars(llm_api_config)
                llm = import_helper.LLMCaller(backend=llm_backend, **llm_api_config)

            # 创建Agent
            agents = import_helper.create_agents(
                num_agents=num_agents,
                malicious_ratio=malicious_ratio,
                llm_caller=llm,
                role_configs=[],
                random_assignment=True
            )

            # 如果需要确保leader是诚实/恶意的，强制设置第一个agent
            if leader_type == 'malicious' and not agents[0].is_malicious:
                # 将第一个agent设为恶意，并调整其他agent
                agents[0].is_malicious = True
                # 从诚实agent中随机选一个改为恶意以保持总数
                for i in range(1, len(agents)):
                    if not agents[i].is_malicious:
                        agents[i].is_malicious = False
                        break
            elif leader_type == 'honest' and agents[0].is_malicious:
                # 将第一个agent设为诚实，并调整其他agent
                agents[0].is_malicious = False
                # 从恶意agent中随机选一个改为诚实以保持总数
                for i in range(1, len(agents)):
                    if agents[i].is_malicious:
                        agents[i].is_malicious = True
                        break

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

            # 如果是快速测试，限制任务数
            if self.config.get('quick_test', False):
                num_tasks = min(3, len(all_tasks))

            # 运行任务
            task_results = []
            for i, task in enumerate(all_tasks[:num_tasks], 1):
                print(f"\n  任务 {i}/{num_tasks}: {task['content'][:60]}...")
                print(f"  类型: {task.get('type', 'unknown')}, 难度: {task.get('difficulty', 'unknown')}")

                # 记录leader信息
                leader_idx = bft.current_view % len(agents)
                leader_is_malicious = agents[leader_idx].is_malicious

                result = bft.run(task)
                result['leader_is_malicious'] = leader_is_malicious
                result['task_type'] = task.get('type', 'unknown')
                result['task_difficulty'] = task.get('difficulty', 'unknown')
                result['expected_behavior'] = task.get('expected_behavior', 'correct')

                task_results.append(result)

                # 打印关键统计
                if result['success']:
                    prep_data = result['latency_data'].get('prepare', {})
                    y_count = prep_data.get('y_count', 0)
                    n_count = prep_data.get('n_count', 0)
                    print(f"    结果: 成功 | Y票: {y_count}, N票: {n_count}")
                else:
                    print(f"    结果: 失败 | 视图切换: {result.get('view_changes', 0)}次")

                time.sleep(0.5)

            # 统计
            success_count = sum(1 for r in task_results if r['success'])

            # 计算各种统计指标
            successful_results = [r for r in task_results if r['success']]
            all_results_for_voting = task_results  # 包括失败的任务也分析投票

            # 投票统计（包括成功和失败的任务）
            vote_details = []
            y_counts = []
            n_counts = []
            margins = []  # 距离2f+1阈值的余量

            # 计算阈值
            f = malicious_count
            quorum = 2 * f + 1

            for r in all_results_for_voting:
                # 安全获取latency_data
                latency_data = r.get('latency_data', {})
                if not latency_data:
                    # 如果没有latency_data（任务失败），跳过或使用默认值
                    if not r.get('success'):
                        # 失败的任务，记录默认值
                        y_count = 0
                        n_count = num_agents  # 假设所有人都投了N票
                    else:
                        # 成功但无数据，跳过
                        continue
                else:
                    prep_data = latency_data.get('prepare', {})
                    y_count = prep_data.get('y_count', 0)
                    n_count = prep_data.get('n_count', 0)

                total_votes = y_count + n_count

                # 计算余量（距离阈值还差多少票）
                margin = y_count - quorum if y_count >= quorum else quorum - y_count

                vote_details.append({
                    'task_success': r.get('success', False),
                    'y_count': y_count,
                    'n_count': n_count,
                    'total_votes': total_votes,
                    'quorum': quorum,
                    'margin': margin,
                    'is_consensus_reached': y_count >= quorum
                })

                y_counts.append(y_count)
                n_counts.append(n_count)
                margins.append(margin)

            # 计算平均值
            if successful_results:
                avg_total_latency = sum(r['latency_data']['total'] for r in successful_results) / len(successful_results)
                avg_prepare_latency = sum(r['latency_data']['prepare']['latency'] for r in successful_results) / len(successful_results)
                avg_commit_latency = sum(r['latency_data']['commit']['latency'] for r in successful_results) / len(successful_results)
                avg_view_changes = sum(r['view_changes'] for r in successful_results) / len(successful_results)
            else:
                avg_total_latency = 0
                avg_prepare_latency = 0
                avg_commit_latency = 0
                avg_view_changes = 0

            # 投票统计
            avg_y_count = sum(y_counts) / len(y_counts) if y_counts else 0
            avg_n_count = sum(n_counts) / len(n_counts) if n_counts else 0
            avg_margin = sum(margins) / len(margins) if margins else 0
            min_margin = min(margins) if margins else 0

            print(f"\n  结果汇总:")
            print(f"    成功: {success_count}/{len(task_results)} ({success_count/len(task_results)*100:.1f}%)")
            print(f"    平均总延迟: {avg_total_latency:.3f}秒")
            print(f"    平均视图切换: {avg_view_changes:.1f}次")
            print(f"  投票统计:")
            print(f"    法定人数阈值(2f+1): {quorum}")
            print(f"    平均Y票: {avg_y_count:.1f}, 平均N票: {avg_n_count:.1f}")
            print(f"    平均余量: +{avg_margin:.1f}票 (距离阈值)")
            print(f"    最小余量: +{min_margin:.1f}票 (最接近阈值的一次)")

            return {
                'config': {
                    'num_agents': num_agents,
                    'malicious_count': malicious_count,
                    'malicious_ratio': malicious_ratio,
                    'leader_type': leader_type,
                    'network_delay': network_delay,
                    'llm_backend': llm_backend
                },
                'task_results': task_results,
                'vote_details': vote_details,
                'summary': {
                    'total_tasks': len(task_results),
                    'success_count': success_count,
                    'success_rate': success_count / len(task_results) if len(task_results) > 0 else 0,
                    'avg_total_latency': avg_total_latency,
                    'avg_prepare_latency': avg_prepare_latency,
                    'avg_commit_latency': avg_commit_latency,
                    'avg_view_changes': avg_view_changes,
                    # 投票统计
                    'quorum_threshold': quorum,
                    'avg_y_count': avg_y_count,
                    'avg_n_count': avg_n_count,
                    'avg_margin': avg_margin,
                    'min_margin': min_margin,
                }
            }

        finally:
            # 恢复工作目录
            os.chdir(original_dir)

    def _generate_filename(self, timestamp: str) -> str:
        """生成包含实验信息的文件名"""
        exp_name = self.config.get('experiment_name', 'fault_tolerance_test')
        return f"{exp_name}_{timestamp}"

    def _save_results(self) -> str:
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

        print(f"\n{'='*80}")
        print(f"结果已保存: {output_file}")
        print(f"{'='*80}")

        # 也保存为latest
        latest_file = f"{self.output_dir}/data/fault_tolerance_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_file

    def run_quick_test(self):
        """运行快速测试（使用Mock LLM）"""
        print("\n快速测试模式（使用Mock LLM）")
        print("="*60)

        # 简化配置
        self.config = {
            'experiment_name': 'fault_tolerance_quick_test',
            'description': '快速测试容错边界',
            'variables': {
                'num_agents': [7],
                'malicious_count': [0, 1, 2],
                'leader_type': ['honest'],  # 只测试诚实leader
                'network_delay': [[10, 100]],
                'llm_backend': ['mock']
            },
            'tasks': {
                'file': 'tricky_questions.json',
                'num_tasks': 3,
                'shuffle': False
            },
            'global': {
                'timeout': 30.0,
                'max_retries': 5,
                'mock_accuracy': 0.7  # Mock LLM准确率较低，模拟刁钻问题
            }
        }
        self.config['quick_test'] = True

        self.run()

    def _analyze_results(self, result_file: str):
        """分析结果并生成可视化"""
        print(f"\n{'='*80}")
        print(f"分析实验结果")
        print(f"{'='*80}\n")

        # 加载结果
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取实验元数据
        # experiment_name = data.get('experiment_name', 'fault_tolerance_test')
        # timestamp = data.get('timestamp', datetime.now().isoformat())
        # llm_backend = data.get('config', {}).get('variables', {}).get('llm_backend', ['unknown'])[0]
        # num_agents = data.get('config', {}).get('variables', {}).get('num_agents', [9])[0]

        # 提取并整理数据
        records = []
        for exp_result in data['results']:
            config = exp_result['config']
            summary = exp_result['summary']

            # 安全地提取值，确保类型正确
            def safe_get_float(d, key, default=0.0):
                val = d.get(key, default)
                if isinstance(val, dict):
                    print(f"Warning: {key} is dict, using default")
                    return default
                try:
                    return float(val or 0)
                except (TypeError, ValueError):
                    return default

            record = {
                'malicious_count': config['malicious_count'],
                'malicious_ratio': config['malicious_ratio'],  # 从config中提取
                'leader_type': config['leader_type'],
                'num_agents': config['num_agents'],
                'success_rate': safe_get_float(summary, 'success_rate', 0.0),
                'avg_total_latency': safe_get_float(summary, 'avg_total_latency', 0.0),
                'avg_view_changes': safe_get_float(summary, 'avg_view_changes', 0.0),
                # 投票统计
                'quorum_threshold': safe_get_float(summary, 'quorum_threshold', 0),
                'avg_y_count': safe_get_float(summary, 'avg_y_count', 0),
                'avg_n_count': safe_get_float(summary, 'avg_n_count', 0),
                'avg_margin': safe_get_float(summary, 'avg_margin', 0),
                'min_margin': safe_get_float(summary, 'min_margin', 0),
                'vote_details': exp_result.get('vote_details', []),
            }
            records.append(record)

        # 分别分析honest leader和malicious leader
        honest_leader_results = [r for r in records if r['leader_type'] == 'honest']
        malicious_leader_results = [r for r in records if r['leader_type'] == 'malicious']

        # 打印统计表格
        print(f"{'='*100}")
        print(f"实验结果汇总表")
        print(f"{'='*100}")

        print(f"\n【诚实Leader场景】")
        print(f"{'恶意':<6} {'恶意比例':<10} {'成功率':<10} {'Y/N平均':<10} {'平均余量':<12} {'最小余量':<10}")
        print(f"{'节点数':<6} {'':<10} {'':<10} {'投票':<10} {'(2f+1)':<12} {'(最危险)':<10}")
        print(f"{'-'*70}")
        for r in sorted(honest_leader_results, key=lambda x: x['malicious_count']):
            # 安全获取值，避免None或dict类型错误
            avg_y = r.get('avg_y_count', 0) or 0
            avg_n = r.get('avg_n_count', 0) or 0
            avg_marg = r.get('avg_margin', 0) or 0
            min_marg = r.get('min_margin', 0) or 0

            # 确保是数字类型
            avg_y = float(avg_y) if not isinstance(avg_y, dict) else 0
            avg_n = float(avg_n) if not isinstance(avg_n, dict) else 0
            avg_marg = float(avg_marg) if not isinstance(avg_marg, dict) else 0
            min_marg = float(min_marg) if not isinstance(min_marg, dict) else 0

            print(f"{r['malicious_count']:<6} {r['malicious_ratio']:>8.1%} "
                  f"{r['success_rate']:>8.1%} {avg_y:>4.0f}/{avg_n:<4.0f} "
                  f"+{avg_marg:>5.1f}票    +{min_marg:>5.1f}票")

        if malicious_leader_results:
            print(f"\n【恶意Leader场景】")
            print(f"{'恶意':<6} {'恶意比例':<10} {'成功率':<10} {'Y/N平均':<10} {'平均余量':<12} {'最小余量':<10}")
            print(f"{'节点数':<6} {'':<10} {'':<10} {'投票':<10} {'(2f+1)':<12} {'(最危险)':<10}")
            print(f"{'-'*70}")
            for r in sorted(malicious_leader_results, key=lambda x: x['malicious_count']):
                # 安全获取值
                avg_y = r.get('avg_y_count', 0) or 0
                avg_n = r.get('avg_n_count', 0) or 0
                avg_marg = r.get('avg_margin', 0) or 0
                min_marg = r.get('min_margin', 0) or 0

                # 确保是数字类型
                avg_y = float(avg_y) if not isinstance(avg_y, dict) else 0
                avg_n = float(avg_n) if not isinstance(avg_n, dict) else 0
                avg_marg = float(avg_marg) if not isinstance(avg_marg, dict) else 0
                min_marg = float(min_marg) if not isinstance(min_marg, dict) else 0

                print(f"{r['malicious_count']:<6} {r['malicious_ratio']:>8.1%} "
                      f"{r['success_rate']:>8.1%} {avg_y:>4.0f}/{avg_n:<4.0f} "
                      f"+{avg_marg:>5.1f}票    +{min_marg:>5.1f}票")

        print(f"\n{'='*100}\n")

        # 绘图（暂时禁用，matplotlib兼容性问题）
        print(f"生成可视化图表...")
        print(f"注意：由于matplotlib兼容性问题，复杂可视化暂时禁用")
        print(f"所有数据已保存到JSON文件，可使用其他工具（如Excel）进行可视化")
        # plotter = Plotter(output_dir=f"{self.output_dir}/figures")
        # self._plot_voting_analysis(...)
        print(f"\n数据已保存到: {self.output_dir}/data/")
        print(f"建议使用Python pandas/matplotlib 或 Excel 进行后续可视化分析")

    def _plot_voting_analysis(
        self,
        honest_results: List[Dict],
        malicious_results: List[Dict],
        plotter: Plotter,
        timestamp: str = None,
        experiment_name: str = "fault_tolerance_test",
        llm_backend: str = "unknown",
        num_agents: int = 9
    ):
        """绘制投票分析和容错边界可视化"""
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

        # 按恶意比例排序
        honest_results.sort(key=lambda x: x['malicious_ratio'])
        malicious_results.sort(key=lambda x: x['malicious_ratio'])

        # 生成带时间戳和配置的文件名
        if timestamp:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%Y%m%d_%H%M%S')
        else:
            time_str = datetime.now().strftime('%Y%m%d_%H%M%S')

        filename = f"fault_tolerance_voting_analysis_{experiment_name}_{num_agents}agents_{llm_backend}_{time_str}.png"

        # 调试：打印关键数据类型
        print(f"\n[调试] 绘图参数:")
        print(f"  honest_results数量: {len(honest_results)}")
        print(f"  malicious_results数量: {len(malicious_results)}")
        print(f"  plotter.output_dir类型: {type(plotter.output_dir)}")

        # 创建2x3子图
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        fig.suptitle('BFT4Agent 容错边界与投票分析（刁钻问题场景）', fontsize=16, fontweight='bold')

        # ===== 图1: 成功率 vs 恶意比例 =====
        ax1 = fig.add_subplot(gs[0, 0])
        x_data = [float(r['malicious_ratio']) for r in honest_results]
        y_data = [float(r['success_rate']) for r in honest_results]
        ax1.plot(x_data, y_data, marker='o', linewidth=2.5, markersize=8,
                color='#2E86AB', label='诚实Leader')
        if malicious_results:
            x_m = [float(r['malicious_ratio']) for r in malicious_results]
            y_m = [float(r['success_rate']) for r in malicious_results]
            ax1.plot(x_m, y_m, marker='s', linewidth=2.5, markersize=8,
                    color='#A23B72', label='恶意Leader')
        ax1.axvline(x=1/3, color='r', linestyle='--', alpha=0.5, label='理论阈值(33%)')
        ax1.axhline(y=2/3, color='g', linestyle=':', alpha=0.3, label='最低成功阈值(66.7%)')
        ax1.set_xlabel('恶意节点比例', fontsize=11)
        ax1.set_ylabel('共识成功率', fontsize=11)
        ax1.set_title('容错边界：成功率 vs 恶意比例', fontsize=12, fontweight='bold')
        ax1.set_ylim([0, 1.05])
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=9)

        # ===== 图1: 成功率 vs 恶意比例 =====
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot([r['malicious_ratio'] for r in honest_results],
                [r['success_rate'] for r in honest_results],
                marker='o', linewidth=2.5, markersize=8, color='#2E86AB',
                label='诚实Leader')
        if malicious_results:  # 只有在有恶意Leader数据时才绘制
            ax1.plot([r['malicious_ratio'] for r in malicious_results],
                    [r['success_rate'] for r in malicious_results],
                    marker='s', linewidth=2.5, markersize=8, color='#A23B72',
                    label='恶意Leader')
        ax1.axvline(x=1/3, color='r', linestyle='--', alpha=0.5, label='理论阈值(33%)')
        ax1.axhline(y=2/3, color='g', linestyle=':', alpha=0.3, label='最低成功阈值(66.7%)')
        ax1.set_xlabel('恶意节点比例', fontsize=11)
        ax1.set_ylabel('共识成功率', fontsize=11)
        ax1.set_title('容错边界：成功率 vs 恶意比例', fontsize=12, fontweight='bold')
        ax1.set_ylim([0, 1.05])
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=9)

        # ===== 图2: 投票分布（Y票 vs N票） =====
        ax2 = fig.add_subplot(gs[0, 1])
        malicious_ratios = [r['malicious_ratio'] for r in honest_results]
        y_counts_honest = [float(r.get('avg_y_count', 0) or 0) for r in honest_results]
        n_counts_honest = [float(r.get('avg_n_count', 0) or 0) for r in honest_results]

        x = range(len(malicious_ratios))
        width = 0.35

        ax2.bar([i - width/2 for i in x], y_counts_honest, width,
               label='Y票（同意）', color='#2E86AB', alpha=0.8)
        ax2.bar([i + width/2 for i in x], n_counts_honest, width,
               label='N票（反对）', color='#C73E1D', alpha=0.8)

        # 添加2f+1阈值线
        for i, r in enumerate(honest_results):
            quorum = r['quorum_threshold']
            ax2.axhline(y=quorum, xmin=(i-0.5)/len(malicious_ratios),
                       xmax=(i+0.5)/len(malicious_ratios),
                       color='r', linestyle='--', alpha=0.3, linewidth=2)
            # 标注阈值
            if i == 0:
                ax2.text(i, quorum + 0.2, f'2f+1={quorum}',
                        ha='center', fontsize=8, color='r')

        ax2.set_xlabel('恶意节点比例', fontsize=11)
        ax2.set_ylabel('平均票数', fontsize=11)
        ax2.set_title('投票分布：Y票 vs N票（诚实Leader）', fontsize=12, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f'{int(r*100)}%' for r in malicious_ratios])
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3, axis='y')

        # ===== 图3: 余量分析（距离2f+1的余量） =====
        ax3 = fig.add_subplot(gs[0, 2])
        margins_avg = [float(r.get('avg_margin', 0) or 0) for r in honest_results]
        margins_min = [float(r.get('min_margin', 0) or 0) for r in honest_results]

        ax3.plot(malicious_ratios, margins_avg,
                marker='o', linewidth=2.5, markersize=8, color='#2E86AB',
                label='平均余量')
        ax3.plot(malicious_ratios, margins_min,
                marker='v', linewidth=2, markersize=6, color='#F18F01',
                label='最小余量（最危险）')
        ax3.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='零余量（危险线）')

        # 添加数值标签
        for i, (ratio, avg, min_m) in enumerate(zip(malicious_ratios, margins_avg, margins_min)):
            ax3.annotate(f'+{avg:.1f}', (ratio, avg),
                        textcoords="offset points", xytext=(0, 5),
                        ha='center', fontsize=8, color='#2E86AB')
            ax3.annotate(f'+{min_m:.1f}', (ratio, min_m),
                        textcoords="offset points", xytext=(0, -15),
                        ha='center', fontsize=8, color='#F18F01')

        ax3.set_xlabel('恶意节点比例', fontsize=11)
        ax3.set_ylabel('余量（票数）', fontsize=11)
        ax3.set_title('容错余量：距离2f+1阈值还差多少票', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=9)

        # ===== 图4: 诚实 vs 恶意Leader投票对比 =====
        ax4 = fig.add_subplot(gs[1, 0])

        # 确保数据是数字类型
        y_counts_honest = [float(r.get('avg_y_count', 0) or 0) for r in honest_results]

        ax4.plot(malicious_ratios, y_counts_honest,
                marker='o', linewidth=2.5, markersize=7, color='#2E86AB',
                label='诚实Leader-Y票')

        if malicious_results:  # 只有在有恶意Leader数据时才绘制
            y_counts_malicious = [float(r.get('avg_y_count', 0) or 0) for r in malicious_results]
            ax4.plot(malicious_ratios, y_counts_malicious,
                    marker='s', linewidth=2.5, markersize=7, color='#A23B72',
                    label='恶意Leader-Y票')

        # 添加阈值线
        for i, r in enumerate(honest_results):
            quorum = r['quorum_threshold']
            ax4.axhline(y=quorum, xmin=(i-0.5)/len(malicious_ratios),
                       xmax=(i+0.5)/len(malicious_ratios),
                       color='r', linestyle='--', alpha=0.3, linewidth=1.5)

        ax4.set_xlabel('恶意节点比例', fontsize=11)
        ax4.set_ylabel('平均Y票数', fontsize=11)
        if malicious_results:
            ax4.set_title('Leader类型对比：Y票获取能力', fontsize=12, fontweight='bold')
        else:
            ax4.set_title('Leader类型对比：Y票获取能力（仅诚实Leader）', fontsize=12, fontweight='bold')
        ax4.set_xticks(malicious_ratios)
        ax4.set_xticklabels([f'{int(r*100)}%' for r in malicious_ratios])
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=9)

        # ===== 图5: 余量柱状图（清晰展示安全边界） =====
        ax5 = fig.add_subplot(gs[1, 1])

        categories = [f'{int(r*100)}%\n({r["malicious_count"]}个)' for r in honest_results]
        x_pos = range(len(categories))

        # 确保数据是数字类型
        margins_avg_safe = [float(r.get('avg_margin', 0) or 0) for r in honest_results]

        bars = ax5.bar(x_pos, margins_avg_safe, color='#2E86AB', alpha=0.7,
                      edgecolor='black', linewidth=1.5, label='平均余量')

        # 添加阈值线
        ax5.axhline(y=0, color='r', linestyle='--', linewidth=2, label='危险线（零余量）')

        # 添加数值标签和颜色指示
        for i, (bar, margin) in enumerate(zip(bars, margins_avg_safe)):
            height = bar.get_height()
            # 根据余量大小设置颜色（余量越小越危险）
            if margin < 1:
                color = '#C73E1D'  # 红色 - 危险
            elif margin < 2:
                color = '#F18F01'  # 橙色 - 警告
            else:
                color = '#2E86AB'  # 蓝色 - 安全
            bar.set_color(color)

            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'+{margin:.1f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax5.set_xlabel('恶意节点比例', fontsize=11)
        ax5.set_ylabel('平均余量（票数）', fontsize=11)
        ax5.set_title('安全边界可视化（余量越大越安全）', fontsize=12, fontweight='bold')
        ax5.set_xticks(x_pos)
        ax5.set_xticklabels(categories)
        ax5.legend(fontsize=9)
        ax5.grid(True, alpha=0.3, axis='y')

        # 添加颜色说明
        ax5.text(0.02, 0.98, '🔴 危险区（余量<1）', transform=ax5.transAxes,
                fontsize=9, color='#C73E1D', va='top')
        ax5.text(0.02, 0.93, '🟠 警告区（余量1-2）', transform=ax5.transAxes,
                fontsize=9, color='#F18F01', va='top')
        ax5.text(0.02, 0.88, '🔵 安全区（余量>2）', transform=ax5.transAxes,
                fontsize=9, color='#2E86AB', va='top')

        # ===== 图6: 详细投票散点图（所有投票点） =====
        ax6 = fig.add_subplot(gs[1, 2])

        # 检查是否有投票详情数据
        has_vote_data = any(r.get('vote_details') for r in honest_results)

        if has_vote_data:
            # 收集所有投票详情
            for r in honest_results:
                malicious_ratio = r['malicious_ratio']
                quorum = r['quorum_threshold']
                vote_details = r.get('vote_details', [])

                for vd in vote_details:
                    y_count = vd['y_count']
                    is_success = vd['task_success']

                    # 根据是否成功设置颜色
                    color = '#2E86AB' if is_success else '#C73E1D'
                    marker = 'o' if is_success else 'x'
                    alpha = 0.8 if is_success else 0.5

                    ax6.scatter(malicious_ratio, y_count,
                              marker=marker, s=100, color=color, alpha=alpha,
                              edgecolors='black', linewidth=0.5)

            # 添加阈值线
            for i, r in enumerate(honest_results):
                quorum = r['quorum_threshold']
                ax6.axhline(y=quorum, xmin=(i-0.5)/len(malicious_ratios),
                           xmax=(i+0.5)/len(malicious_ratios),
                           color='r', linestyle='--', alpha=0.5, linewidth=2)

            ax6.set_xlabel('恶意节点比例', fontsize=11)
            ax6.set_ylabel('实际Y票数', fontsize=11)
            ax6.set_title('每次投票详细分布（圆=成功，叉=失败）', fontsize=12, fontweight='bold')
            ax6.set_xticks(malicious_ratios)
            ax6.set_xticklabels([f'{int(r*100)}%' for r in malicious_ratios])

            # 添加图例
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#2E86AB',
                       markersize=10, label='成功达成共识', markeredgecolor='black'),
                Line2D([0], [0], marker='x', color='w', markerfacecolor='#C73E1D',
                       markersize=10, label='未达成共识', markeredgecolor='black'),
                Line2D([0], [0], color='r', linestyle='--', label='2f+1阈值')
            ]
            ax6.legend(handles=legend_elements, fontsize=9)
        else:
            # 如果没有投票详情数据，显示提示信息
            ax6.text(0.5, 0.5, '无投票详情数据\n请检查任务执行结果',
                    ha='center', va='center', fontsize=12,
                    transform=ax6.transAxes)
            ax6.set_title('每次投票详细分布（数据不可用）', fontsize=12, fontweight='bold')
            ax6.set_xticks([])
            ax6.set_yticks([])

        ax6.grid(True, alpha=0.3)

        # 保存图表
        output_file = f"{plotter.output_dir}/{filename}"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  已保存: {output_file}")

        # 也保存简化版本
        simple_filename = f"fault_tolerance_latest_{llm_backend}.png"
        simple_output_file = f"{plotter.output_dir}/{simple_filename}"
        plt.savefig(simple_output_file, dpi=300, bbox_inches='tight')
        print(f"  已保存（简化名称）: {simple_output_file}")

        plt.close()
