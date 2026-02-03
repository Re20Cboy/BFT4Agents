"""
绘制Mock vs Qwen LLM延迟对比图
改进版本：更大字体、更好配色、全英文、无标题
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
from pathlib import Path

# 设置学术论文风格（参考 plot_latency.py）
plt.style.use('seaborn-v0_8-paper')

# 更新配置 - 使用更大字体
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.labelsize': 14,        # 从12增加到14
    'axes.titlesize': 0,         # 移除标题
    'legend.fontsize': 11,       # 从10增加到11
    'xtick.labelsize': 12,       # 从10增加到12
    'ytick.labelsize': 12,       # 从10增加到12
    'lines.linewidth': 2.5,      # 从1.8增加到2.5
    'lines.markersize': 9,       # 从7增加到9
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--'
})

matplotlib.rcParams['axes.unicode_minus'] = False

# 改进的配色方案（参考plot_latency.py风格）
MOCK_COLOR = '#2E86AB'      # 蓝色 - Mock LLM（保持，用户说还行）
QWEN_COLOR = '#d6604d'      # 深红色 - Qwen LLM（参考plot_latency.py的红色调）
LLM_REGION_COLOR = '#d6604d'  # 使用Qwen的红色，半透明填充
ERROR_BAR_COLOR = '#666666'   # 灰色 - Error bar（更柔和）

def load_experiment_data(file_path):
    """加载实验数据并提取统计信息"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for exp_result in data['results']:
        malicious_ratio = exp_result['config']['malicious_ratio']
        malicious_count = exp_result['config']['malicious_count']

        # 提取每个任务的延迟
        task_latencies = []
        for task_result in exp_result['task_results']:
            if task_result['success']:
                task_latencies.append(task_result['latency_data']['total'])

        if task_latencies:
            results.append({
                'malicious_ratio': malicious_ratio,
                'malicious_count': malicious_count,
                'mean': np.mean(task_latencies),
                'std': np.std(task_latencies) if len(task_latencies) > 1 else 0,
                'latencies': task_latencies
            })

    # 按恶意比例排序
    results.sort(key=lambda x: x['malicious_ratio'])
    return results

def plot_llm_comparison():
    """绘制Mock vs Qwen LLM对比图 - 改进版本"""

    # 加载数据
    mock_data = load_experiment_data('ex/results/data/malicious_vs_latency_experiment_mock_20260203_100637.json')
    qwen_data = load_experiment_data('ex/results/data/malicious_vs_latency_experiment_20260130_110804.json')

    # 提取数据
    ratios = [d['malicious_ratio'] for d in mock_data]
    mock_means = [d['mean'] for d in mock_data]
    mock_stds = [d['std'] for d in mock_data]
    qwen_means = [d['mean'] for d in qwen_data]
    qwen_stds = [d['std'] for d in qwen_data]
    counts = [d['malicious_count'] for d in mock_data]

    # 创建图表（稍大一些）
    fig, ax = plt.subplots(figsize=(8, 6))

    # 设置log尺度
    ax.set_yscale('log')

    # 绘制填充区域（LLM后端延迟）- 使用红色，更透明
    ax.fill_between(ratios, mock_means, qwen_means,
                    alpha=0.2, color=QWEN_COLOR,
                    label='LLM Backend Overhead')

    # 绘制Mock LLM折线 - 使用蓝色
    ax.errorbar(ratios, mock_means, yerr=mock_stds,
               fmt='o-', linewidth=2.5, markersize=9,
               capsize=4, capthick=2,
               color=MOCK_COLOR,
               ecolor=ERROR_BAR_COLOR, elinewidth=1.5,
               label='Mock LLM (System Baseline)')

    # 绘制Qwen LLM折线 - 使用深红色
    ax.errorbar(ratios, qwen_means, yerr=qwen_stds,
               fmt='s-', linewidth=2.5, markersize=9,
               capsize=4, capthick=2,
               color=QWEN_COLOR,
               ecolor=ERROR_BAR_COLOR, elinewidth=1.5,
               label='Qwen LLM (Real Backend)')

    # 设置标签（全英文，简洁）
    ax.set_xlabel('Malicious Node Ratio', fontweight='bold')
    ax.set_ylabel('Total Latency (seconds, log scale)', fontweight='bold')
    # 不设置标题

    # 设置x轴刻度
    ax.set_xticks(ratios)
    ax.set_xticklabels([f'{int(r*100)}%\n({c})'
                       for r, c in zip(ratios, counts)])

    # 网格设置
    ax.grid(True, linestyle='--', alpha=0.3, which='both')

    # 图例设置（放在左上角，带阴影）
    ax.legend(fontsize=11, loc='upper left',
             frameon=True, shadow=True,
             fancybox=True, framealpha=0.95)

    # 在图中添加延迟倍数标注（更简洁）
    for i, (r, mock, qwen) in enumerate(zip(ratios, mock_means, qwen_means)):
        ratio_val = qwen / mock
        mid_y = np.sqrt(mock * qwen)

        # 只标注部分倍数，避免太拥挤
        if i % 2 == 0:  # 每隔一个标注
            ax.annotate(f'{ratio_val:.0f}x',
                       xy=(r, mid_y),
                       xytext=(0, 0),
                       textcoords='offset points',
                       fontsize=9,
                       color='#333333',
                       fontweight='bold',
                       ha='center',
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='white',
                                alpha=0.7,
                                edgecolor='gray',
                                linewidth=0.5))

    # 设置y轴范围以更好显示数据
    ax.set_ylim([min(mock_means) * 0.5, max(qwen_means) * 1.5])

    plt.tight_layout()

    # 保存图表
    output_dir = Path('ex/results/figures')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'mock_vs_qwen_llm_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved comparison plot: {output_file}")

    # 同时保存PDF格式（用于论文）
    output_pdf = output_dir / 'mock_vs_qwen_llm_comparison.pdf'
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved PDF version: {output_pdf}")

    plt.close()

    return output_file, output_pdf

if __name__ == '__main__':
    print("\nGenerating Mock vs Qwen LLM comparison plot (improved version)...\n")
    plot_llm_comparison()
    print("\nPlot generation completed!\n")
