"""
绘图工具
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class Plotter:
    """实验结果绘图工具"""

    def __init__(self, output_dir: str = "ex/results/figures"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_latency_summary(self, df: pd.DataFrame):
        """绘制延迟综合图表"""
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        fig.suptitle('BFT4Agent 延迟实验结果', fontsize=16)

        # 1. 端到端延迟分布
        ax = axes[0, 0]
        ax.hist(df['total_latency'], bins=15, color='steelblue', alpha=0.7, edgecolor='black')
        ax.axvline(df['total_latency'].mean(), color='red', linestyle='--',
                  label=f"平均: {df['total_latency'].mean():.3f}s")
        ax.set_xlabel('延迟 (秒)')
        ax.set_ylabel('频数')
        ax.set_title('端到端延迟分布')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. 各阶段延迟对比
        ax = axes[0, 1]
        phase_means = df[['pre_prepare_latency', 'prepare_latency', 'commit_latency']].mean()
        phase_means.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                       edgecolor='black', linewidth=1.5)
        ax.set_ylabel('平均延迟 (秒)')
        ax.set_title('各阶段平均延迟')
        ax.set_xticklabels(['PRE-PREPARE', 'PREPARE', 'COMMIT'], rotation=0)
        ax.grid(axis='y', alpha=0.3)

        # 3. 各阶段延迟占比
        ax = axes[0, 2]
        total = phase_means.sum()
        sizes = phase_means.values / total * 100
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        labels = [f'{l}\n({s:.1f}%)' for l, s in zip(['PRE-PREPARE', 'PREPARE', 'COMMIT'], sizes)]
        ax.pie(phase_means, labels=labels, colors=colors, autopct='', startangle=90)
        ax.set_title('各阶段延迟占比')

        # 4. 成功率
        ax = axes[1, 0]
        success_count = df['task_success'].sum()
        total_count = len(df)
        ax.bar(['成功', '失败'], [success_count, total_count - success_count],
              color=['green', 'red'], alpha=0.7)
        ax.set_ylabel('任务数')
        ax.set_title(f'成功率: {success_count/total_count:.1%}')
        ax.grid(axis='y', alpha=0.3)

        # 5. 投票统计
        ax = axes[1, 1]
        total_y = df['prepare_y_count'].sum()
        total_n = df['prepare_n_count'].sum()
        ax.bar(['Y (同意)', 'N (拒绝)'], [total_y, total_n],
              color=['seagreen', 'crimson'], alpha=0.7)
        ax.set_ylabel('投票数')
        ax.set_title('PREPARE阶段投票统计')
        ax.grid(axis='y', alpha=0.3)

        # 6. 关键指标文本
        ax = axes[1, 2]
        ax.axis('off')
        summary_text = f"""
        关键指标
        {'='*20}

        总任务数: {total_count}
        成功任务: {success_count}
        成功率: {success_count/total_count:.1%}

        平均端到端延迟: {df['total_latency'].mean():.3f}s
        最小/最大延迟: {df['total_latency'].min():.3f}s / {df['total_latency'].max():.3f}s

        PRE-PREPARE: {df['pre_prepare_latency'].mean():.3f}s
        PREPARE: {df['prepare_latency'].mean():.3f}s
        COMMIT: {df['commit_latency'].mean():.3f}s

        总视图切换: {df['view_changes'].sum()} 次
        """
        ax.text(0.1, 0.5, summary_text, fontsize=10,
              family='monospace', verticalalignment='center')

        plt.tight_layout()
        output_file = os.path.join(self.output_dir, 'latency_summary.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  图表已保存: {output_file}")

    def plot_latency_vs_agents(self, df: pd.DataFrame):
        """绘制延迟 vs 节点数"""
        if 'num_agents' not in df.columns or len(df['num_agents'].unique()) <= 1:
            return

        grouped = df.groupby('num_agents')['total_latency'].agg(['mean', 'std'])

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.errorbar(grouped.index, grouped['mean'], yerr=grouped['std'],
                   marker='o', linewidth=2, markersize=8, capsize=5)
        ax.set_xlabel('节点数', fontsize=12)
        ax.set_ylabel('端到端延迟 (秒)', fontsize=12)
        ax.set_title('端到端延迟 vs 节点数', fontsize=14)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_file = os.path.join(self.output_dir, 'latency_vs_agents.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  图表已保存: {output_file}")
