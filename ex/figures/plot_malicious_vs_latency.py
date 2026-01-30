"""
Malicious vs Latency Experiment - Academic Quality Plots
生成符合顶级学术期刊(CCF A, SCI 1区)标准的实验结果图

Experiment: 不同恶意节点比例对系统延迟和性能的影响
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置学术论文风格
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'lines.linewidth': 1.8,
    'lines.markersize': 7,
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--'
})

# 定义学术配色方案
COLORS = {
    'primary': '#2E86AB',      # 深蓝色
    'secondary': '#A23B72',    # 深紫红色
    'success': '#06A77D',      # 深绿色
    'warning': '#F18F01',      # 橙色
    'danger': '#C73E1D',       # 深红色
    'neutral': '#6B7280'       # 灰色
}

def load_experiment_data(file_path):
    """
    加载malicious_vs_latency实验数据

    Args:
        file_path: JSON数据文件路径

    Returns:
        DataFrame: 整理后的实验数据
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {file_path}")

    print(f"加载数据: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []

    # 遍历每个实验配置
    for result in data['results']:
        config = result['config']
        num_agents = config['num_agents']
        malicious_count = config['malicious_count']
        malicious_ratio = config['malicious_ratio']

        # 遍历每个任务结果
        for task in result['task_results']:
            latency_data = task['latency_data']

            records.append({
                'num_agents': num_agents,
                'malicious_count': malicious_count,
                'malicious_ratio': malicious_ratio,
                'malicious_percentage': malicious_ratio * 100,
                'total_latency': latency_data['total'],
                'pre_prepare_latency': latency_data['pre_prepare']['latency'],
                'prepare_latency': latency_data['prepare']['latency'],
                'commit_latency': latency_data['commit']['latency'],
                'view_changes': task.get('view_changes', 0),
                'total_messages': task.get('total_messages', 0),
                'success': task.get('success', False),
                'prepare_y_count': latency_data['prepare'].get('y_count', 0),
                'prepare_n_count': latency_data['prepare'].get('n_count', 0),
                'commit_y_count': latency_data['commit'].get('y_count', 0),
                'commit_n_count': latency_data['commit'].get('n_count', 0),
            })

    df = pd.DataFrame(records)
    print(f"数据加载完成: {len(df)} 条记录")
    print(f"恶意节点比例范围: {df['malicious_percentage'].min():.0f}% - {df['malicious_percentage'].max():.0f}%")

    return df


def plot_fig1_latency_vs_malicious_ratio(df, output_dir):
    """
    图1: 恶意节点比例 vs 总延迟 (核心图)
    展示不同恶意节点比例对系统端到端延迟的影响
    """
    print("\n[图1] 生成恶意节点比例 vs 总延迟图...")

    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    # 按恶意节点比例分组统计
    stats = df.groupby('malicious_percentage')['total_latency'].agg(['mean', 'std', 'min', 'max']).reset_index()

    # 绘制主曲线和误差带
    ax.errorbar(stats['malicious_percentage'], stats['mean'],
                yerr=stats['std'],
                marker='o',
                linewidth=2.5,
                markersize=9,
                capsize=5,
                capthick=2,
                color=COLORS['primary'],
                ecolor=COLORS['primary'],
                alpha=0.8,
                label='Average Latency')

    # 添加最小最大值散点
    ax.scatter(stats['malicious_percentage'], stats['min'],
              marker='_', s=100, color=COLORS['success'], alpha=0.6,
              label='Min Latency', zorder=3)
    ax.scatter(stats['malicious_percentage'], stats['max'],
              marker='_', s=100, color=COLORS['danger'], alpha=0.6,
              label='Max Latency', zorder=3)

    # 设置标签和标题
    ax.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=12)
    ax.set_ylabel('Total Latency (seconds)', fontweight='bold', fontsize=12)
    ax.set_title('Impact of Malicious Node Ratio on System Latency',
                fontweight='bold', fontsize=13)

    # 设置x轴刻度
    ax.set_xticks(stats['malicious_percentage'].values)
    ax.set_xticklabels([f'{int(x)}%' for x in stats['malicious_percentage'].values])

    # 网格和图例
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=1)
    ax.legend(frameon=True, shadow=True, loc='upper left', fontsize=10)

    # 添加统计数据注释
    for idx, row in stats.iterrows():
        ax.annotate(f'{row["mean"]:.1f}s',
                   xy=(row['malicious_percentage'], row['mean']),
                   xytext=(0, 10), textcoords='offset points',
                   ha='center', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow',
                           alpha=0.3, edgecolor='none'))

    plt.tight_layout()
    output_path = output_dir / 'fig1_latency_vs_malicious_ratio.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Saved: {output_path.name}")
    return output_path


def plot_fig2_latency_breakdown(df, output_dir):
    """
    图2: 延迟成分分解图
    展示不同恶意节点比例下,各阶段(pre-prepare, prepare, commit)延迟的变化
    """
    print("\n[图2] 生成延迟成分分解图...")

    fig, ax = plt.subplots(figsize=(8, 6))

    # 准备数据
    malicious_ratios = sorted(df['malicious_percentage'].unique())

    # 计算每个比例下的平均延迟
    pre_prepare_means = []
    prepare_means = []
    commit_means = []
    network_means = []

    for ratio in malicious_ratios:
        subset = df[df['malicious_percentage'] == ratio]

        pre_prepare_means.append(subset['pre_prepare_latency'].mean())
        prepare_means.append(subset['prepare_latency'].mean())
        commit_means.append(subset['commit_latency'].mean())

        # 计算网络延迟(总延迟 - 共识延迟)
        total_mean = subset['total_latency'].mean()
        consensus_mean = (subset['pre_prepare_latency'] +
                         subset['prepare_latency'] +
                         subset['commit_latency']).mean()
        network_means.append(max(0, total_mean - consensus_mean))

    x = np.arange(len(malicious_ratios))
    width = 0.6

    # 堆叠柱状图
    ax.bar(x, pre_prepare_means, width, label='LLM Inference (Pre-Prepare)',
          color=COLORS['primary'], alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.bar(x, prepare_means, width, bottom=pre_prepare_means,
          label='Prepare Phase', color=COLORS['secondary'], alpha=0.85,
          edgecolor='white', linewidth=1.5)

    # 计算prepare的累积高度
    prepare_cumsum = np.array(pre_prepare_means) + np.array(prepare_means)

    ax.bar(x, commit_means, width, bottom=prepare_cumsum,
          label='Commit Phase', color=COLORS['success'], alpha=0.85,
          edgecolor='white', linewidth=1.5)

    # 计算commit的累积高度
    commit_cumsum = prepare_cumsum + np.array(commit_means)

    ax.bar(x, network_means, width, bottom=commit_cumsum,
          label='Network & Others', color=COLORS['neutral'], alpha=0.85,
          edgecolor='white', linewidth=1.5)

    # 设置标签
    ax.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=12)
    ax.set_ylabel('Average Latency (seconds)', fontweight='bold', fontsize=12)
    ax.set_title('Latency Composition Analysis at Different Malicious Ratios',
                fontweight='bold', fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{int(r)}%' for r in malicious_ratios])

    ax.legend(frameon=True, shadow=True, loc='upper left', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = output_dir / 'fig2_latency_breakdown.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Saved: {output_path.name}")
    return output_path


def plot_fig3_view_changes_and_messages(df, output_dir):
    """
    图3: 视图切换次数和消息数量分析
    展示恶意节点比例对共识成本的影响
    """
    print("\n[图3] 生成视图切换和消息数量分析图...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 统计数据
    stats = df.groupby('malicious_percentage').agg({
        'view_changes': ['mean', 'std'],
        'total_messages': ['mean', 'std']
    }).reset_index()
    stats.columns = ['malicious_percentage', 'view_mean', 'view_std', 'msg_mean', 'msg_std']

    x = stats['malicious_percentage'].values

    # 左图: 视图切换次数
    ax1.errorbar(x, stats['view_mean'], yerr=stats['view_std'],
                marker='s', linewidth=2.5, markersize=9,
                capsize=5, capthick=2, color=COLORS['warning'],
                ecolor=COLORS['warning'], alpha=0.8)

    ax1.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Average View Changes', fontweight='bold', fontsize=11)
    ax1.set_title('(a) View Changes Required', fontweight='bold', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{int(v)}%' for v in x])
    ax1.grid(True, linestyle='--', alpha=0.3)

    # 添加数值标签
    for idx, row in stats.iterrows():
        ax1.annotate(f'{row["view_mean"]:.1f}',
                    xy=(row['malicious_percentage'], row['view_mean']),
                    xytext=(0, 10), textcoords='offset points',
                    ha='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow',
                            alpha=0.3, edgecolor='none'))

    # 右图: 总消息数
    ax2.errorbar(x, stats['msg_mean'], yerr=stats['msg_std'],
                marker='^', linewidth=2.5, markersize=9,
                capsize=5, capthick=2, color=COLORS['danger'],
                ecolor=COLORS['danger'], alpha=0.8)

    ax2.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=11)
    ax2.set_ylabel('Average Total Messages', fontweight='bold', fontsize=11)
    ax2.set_title('(b) Communication Overhead', fontweight='bold', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'{int(v)}%' for v in x])
    ax2.grid(True, linestyle='--', alpha=0.3)

    # 添加数值标签
    for idx, row in stats.iterrows():
        ax2.annotate(f'{row["msg_mean"]:.0f}',
                    xy=(row['malicious_percentage'], row['msg_mean']),
                    xytext=(0, 15), textcoords='offset points',
                    ha='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow',
                            alpha=0.3, edgecolor='none'))

    plt.suptitle('Consensus Cost Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / 'fig3_view_changes_and_messages.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Saved: {output_path.name}")
    return output_path


def plot_fig4_vote_analysis(df, output_dir):
    """
    图4: 投票模式分析
    展示Prepare和Commit阶段的Y/N投票分布
    """
    print("\n[图4] 生成投票模式分析图...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 统计投票数据
    stats = df.groupby('malicious_percentage').agg({
        'prepare_y_count': 'mean',
        'prepare_n_count': 'mean',
        'commit_y_count': 'mean',
        'commit_n_count': 'mean'
    }).reset_index()

    x = np.arange(len(stats))
    width = 0.35

    # 左图: Prepare阶段投票
    ax1.bar(x - width/2, stats['prepare_y_count'], width,
           label='Y Votes (Agree)', color=COLORS['success'],
           alpha=0.85, edgecolor='white', linewidth=1.5)
    ax1.bar(x + width/2, stats['prepare_n_count'], width,
           label='N Votes (Reject)', color=COLORS['danger'],
           alpha=0.85, edgecolor='white', linewidth=1.5)

    ax1.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Average Vote Count', fontweight='bold', fontsize=11)
    ax1.set_title('(a) Prepare Phase Voting', fontweight='bold', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{int(r)}%' for r in stats['malicious_percentage']])
    ax1.legend(frameon=True, shadow=True, fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.3, axis='y')

    # 右图: Commit阶段投票
    ax2.bar(x - width/2, stats['commit_y_count'], width,
           label='Y Votes (Agree)', color=COLORS['success'],
           alpha=0.85, edgecolor='white', linewidth=1.5)
    ax2.bar(x + width/2, stats['commit_n_count'], width,
           label='N Votes (Reject)', color=COLORS['danger'],
           alpha=0.85, edgecolor='white', linewidth=1.5)

    ax2.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=11)
    ax2.set_ylabel('Average Vote Count', fontweight='bold', fontsize=11)
    ax2.set_title('(b) Commit Phase Voting', fontweight='bold', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'{int(r)}%' for r in stats['malicious_percentage']])
    ax2.legend(frameon=True, shadow=True, fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.3, axis='y')

    plt.suptitle('Voting Pattern Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / 'fig4_vote_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Saved: {output_path.name}")
    return output_path


def plot_fig5_latency_distribution(df, output_dir):
    """
    图5: 延迟分布箱线图
    展示不同恶意节点比例下延迟的分布情况
    """
    print("\n[图5] 生成延迟分布箱线图...")

    fig, ax = plt.subplots(figsize=(10, 6))

    # 准备数据
    data_to_plot = []
    labels = []
    for ratio in sorted(df['malicious_percentage'].unique()):
        subset = df[df['malicious_percentage'] == ratio]['total_latency']
        data_to_plot.append(subset.values)
        labels.append(f'{int(ratio)}%')

    # 绘制箱线图
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True,
                   widths=0.6, showmeans=True,
                   medianprops=dict(linewidth=2.5, color='white'),
                   meanprops=dict(marker='D', markerfacecolor='#ff6b6b',
                                 markeredgecolor='white', markersize=7),
                   boxprops=dict(linewidth=2),
                   whiskerprops=dict(linewidth=2, color='#2c3e50'),
                   capprops=dict(linewidth=2, color='#2c3e50'),
                   flierprops=dict(marker='o', markersize=4, alpha=0.5))

    # 为每个箱子设置渐变颜色（基于恶意节点比例：比例越高，颜色越深）
    sorted_ratios = sorted(df['malicious_percentage'].unique())
    min_ratio = min(sorted_ratios)
    max_ratio = max(sorted_ratios)

    for i, (patch, ratio) in enumerate(zip(bp['boxes'], sorted_ratios)):
        # 使用Blues色系：恶意节点比例越高，颜色越深
        # ratio范围从5到30，归一化到0.3-0.95的深蓝范围
        normalized_ratio = (ratio - min_ratio) / (max_ratio - min_ratio)
        # 0.3-0.95确保颜色不会太浅也不会太深
        color_intensity = 0.3 + 0.65 * normalized_ratio

        color = plt.cm.Blues(color_intensity)
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
        patch.set_edgecolor('#2c3e50')

    # 调大坐标轴标签字体
    ax.set_xlabel('Malicious Node Ratio (%)', fontweight='bold', fontsize=15)
    ax.set_ylabel('Total Latency (seconds)', fontweight='bold', fontsize=15)
    ax.tick_params(axis='both', labelsize=13)
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = output_dir / 'fig5_latency_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Saved: {output_path.name}")
    return output_path


def generate_summary_table(df, output_dir):
    """
    生成统计摘要表(CSV格式)
    """
    print("\n生成统计摘要表...")

    summary = df.groupby('malicious_percentage').agg({
        'total_latency': ['mean', 'std', 'min', 'max'],
        'pre_prepare_latency': 'mean',
        'prepare_latency': 'mean',
        'commit_latency': 'mean',
        'view_changes': 'mean',
        'total_messages': 'mean',
        'prepare_y_count': 'mean',
        'prepare_n_count': 'mean'
    }).round(3)

    summary.columns = [
        'Total_Latency_Mean', 'Total_Latency_Std', 'Total_Latency_Min', 'Total_Latency_Max',
        'PrePrepare_Latency', 'Prepare_Latency', 'Commit_Latency',
        'View_Changes', 'Total_Messages',
        'Prepare_Y_Count', 'Prepare_N_Count'
    ]

    output_path = output_dir / 'malicious_vs_latency_summary.csv'
    summary.to_csv(output_path, encoding='utf-8-sig')

    print(f"  [OK] Saved: {output_path.name}")

    # 打印预览
    print("\n" + "="*80)
    print("统计摘要表预览:")
    print("="*80)
    print(summary.to_string())
    print("="*80)

    return output_path


def main():
    """主函数"""
    print("="*80)
    print("Malicious vs Latency Experiment - Academic Quality Plots")
    print("="*80)

    # 设置路径
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'results' / 'data'
    output_dir = script_dir.parent / 'results' / 'figures' / 'malicious_vs_latency'
    output_dir.mkdir(exist_ok=True, parents=True)

    # 查找数据文件
    data_files = list(data_dir.glob('malicious_vs_latency_experiment_*.json'))

    if not data_files:
        print(f"\n错误: 在 {data_dir} 中未找到数据文件")
        return

    # 使用最新的数据文件
    data_file = sorted(data_files)[-1]
    print(f"\n使用数据文件: {data_file.name}")

    # 加载数据
    try:
        df = load_experiment_data(data_file)
    except Exception as e:
        print(f"\n错误: 数据加载失败 - {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*80)
    print("开始生成图表...")
    print("="*80)

    # 生成所有图表
    generated_files = []

    try:
        generated_files.append(plot_fig1_latency_vs_malicious_ratio(df, output_dir))
        generated_files.append(plot_fig2_latency_breakdown(df, output_dir))
        generated_files.append(plot_fig3_view_changes_and_messages(df, output_dir))
        generated_files.append(plot_fig4_vote_analysis(df, output_dir))
        generated_files.append(plot_fig5_latency_distribution(df, output_dir))
        generated_files.append(generate_summary_table(df, output_dir))
    except Exception as e:
        print(f"\n错误: 图表生成失败 - {e}")
        import traceback
        traceback.print_exc()
        return

    # 完成
    print("\n" + "="*80)
    print("[OK] All plots generated successfully!")
    print("="*80)
    print(f"\n输出目录: {output_dir.absolute()}")
    print("\n生成的文件:")
    for f in sorted(generated_files):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
    print("="*80)


if __name__ == '__main__':
    main()
