import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import sys
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

def load_data(file_path, label):
    """加载实验数据并返回DataFrame"""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {file_path}")

    print(f"正在加载数据: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    for result in data['results']:
        num_agents = result['config']['num_agents']
        malicious_ratio = result['config']['malicious_ratio']
        for task in result['task_results']:
            latency_data = task['latency_data']
            records.append({
                'num_agents': num_agents,
                'malicious_ratio': malicious_ratio,
                'total_latency': latency_data['total'],
                'pre_prepare': latency_data['pre_prepare']['latency'],
                'prepare': latency_data['prepare']['latency'],
                'commit': latency_data['commit']['latency'],
                'view_changes': task.get('view_changes', 0),
                'total_messages': task.get('total_messages', 0),
                'type': label
            })
    return pd.DataFrame(records)


def get_data_files():
    """自动查找数据文件"""
    # 数据文件目录
    data_dir = Path(__file__).parent.parent / 'results' / 'data'

    if not data_dir.exists():
        raise FileNotFoundError(f"数据目录不存在: {data_dir}")

    # 查找所有JSON文件
    json_files = sorted(data_dir.glob('latency_experiment_*.json'))

    if len(json_files) < 2:
        raise ValueError(f"需要至少2个数据文件进行对比，当前找到 {len(json_files)} 个")

    print(f"\n找到 {len(json_files)} 个数据文件:")
    for f in json_files:
        print(f"  - {f.name}")

    # 根据文件名判断LLM类型
    llm_file = None
    mock_file = None

    for f in json_files:
        # 读取文件内容判断LLM类型
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            llm_backend = data.get('config', {}).get('variables', {}).get('llm_backend', ['unknown'])

            if 'qwen' in str(llm_backend).lower() or 'llm' in str(llm_backend).lower():
                llm_file = f
            elif 'mock' in str(llm_backend).lower():
                mock_file = f

    # 如果无法自动识别，使用时间戳最新的两个文件
    if llm_file is None or mock_file is None:
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        llm_file = json_files[0]
        mock_file = json_files[1]
        print("\n警告: 无法自动识别LLM类型，使用最新的两个文件")

    return llm_file, mock_file


# 获取数据文件路径
try:
    llm_path, mock_path = get_data_files()
    print(f"\n使用数据文件:")
    print(f"  LLM数据: {llm_path.name}")
    print(f"  Mock数据: {mock_path.name}")
except Exception as e:
    print(f"\n错误: {e}")
    print("\n尝试使用默认路径...")
    # 回退到默认路径
    llm_path = Path(__file__).parent.parent / 'results' / 'data' / 'latency_experiment_4-20agents_0-14malicious_20260128_173300.json'
    mock_path = Path(__file__).parent.parent / 'results' / 'data' / 'latency_experiment_4-20agents_0-14malicious_20260128_151318.json'

# 加载两份数据
try:
    df_llm = load_data(llm_path, 'Ours (w/ LLM)')
    df_base = load_data(mock_path, 'Baseline (Mock)')
    df_all = pd.concat([df_llm, df_base])
    print(f"\n数据加载成功:")
    print(f"  LLM数据: {len(df_llm)} 条记录")
    print(f"  Mock数据: {len(df_base)} 条记录")
    print(f"  总记录数: {len(df_all)} 条\n")
except Exception as e:
    print(f"\n错误: 数据加载失败 - {e}")
    sys.exit(1)

# 创建输出目录
output_dir = Path(__file__).parent / 'output'
output_dir.mkdir(exist_ok=True, parents=True)

print("="*70)
print("开始生成图表...")
print("="*70)

# 1. 核心对比图：Ours vs. Baseline (Total Latency)
print("\n[1/4] 生成核心对比图...")
try:
    fig, ax = plt.subplots(figsize=(7, 5))

    df_subset = df_all[df_all['malicious_ratio'] == 0.0]
    sns.lineplot(data=df_subset, x='num_agents', y='total_latency', hue='type', style='type',
                 markers=True, dashes=False, palette='Set1',
                 errorbar='sd', err_style='band', alpha=0.7, ax=ax)

    # 添加数值标注
    for llm_type in df_subset['type'].unique():
        data = df_subset[df_subset['type'] == llm_type].groupby('num_agents')['total_latency'].mean()
        for x, y in data.items():
            ax.annotate(f'{y:.1f}s', xy=(x, y), xytext=(0, 10),
                       textcoords='offset points', ha='center', va='bottom',
                       fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='gray', linewidth=0.5))

    ax.set_xlabel('Number of Agents ($n$)', fontweight='bold')
    ax.set_ylabel('Total Latency (seconds)', fontweight='bold')
    # 去掉标题
    ax.legend(title='Experiment Setup', frameon=True, shadow=True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(True, linestyle='--', alpha=0.3)

    output_path = output_dir / 'comparison_llm_vs_baseline.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] 已保存: {output_path.name}")
except Exception as e:
    print(f"  [ERROR] 错误: {e}")

# 2. 对数坐标系下的可扩展性分析 (Scalability in Log Scale)
print("\n[2/4] 生成对数坐标系可扩展性分析...")
try:
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.lineplot(data=df_all, x='num_agents', y='total_latency', hue='type',
                 style='malicious_ratio', markers=True, palette='Set1',
                 alpha=0.8, linewidth=2, ax=ax)
    ax.set_yscale('log')
    ax.set_xlabel('Number of Agents ($n$)', fontweight='bold')
    ax.set_ylabel('Total Latency (seconds, Log Scale)', fontweight='bold')
    # 去掉标题
    # 图例放在图内左上角
    ax.legend(title='Type & Malicious Ratio', frameon=True, shadow=True, loc='upper left', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.3, which='both')

    output_path = output_dir / 'scalability_log_plot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] 已保存: {output_path.name}")
except Exception as e:
    print(f"  [ERROR] 错误: {e}")

# 3. 延迟成分占比分析 (Latency Composition Analysis)
print("\n[3/4] 生成延迟成分占比分析图...")
try:
    # 准备数据：计算不同配置下的延迟成分占比及标准差
    composition_data = []

    for llm_type in ['Ours (w/ LLM)', 'Baseline (Mock)']:
        df_subset = df_all[df_all['type'] == llm_type]

        for n in [4, 7, 10, 20]:
            for mal_ratio in [0.0, 0.14]:
                df_filtered = df_subset[(df_subset['num_agents'] == n) &
                                       (df_subset['malicious_ratio'] == mal_ratio)]

                if len(df_filtered) > 0:
                    # 计算每个任务的延迟成分占比
                    for _, row in df_filtered.iterrows():
                        llm_time = row['pre_prepare']
                        consensus_time = row['prepare'] + row['commit']
                        total_time = row['total_latency']
                        network_time = total_time - llm_time - consensus_time
                        network_time = max(0, network_time)

                        pct_llm = (llm_time / total_time) * 100
                        pct_consensus = (consensus_time / total_time) * 100
                        pct_network = (network_time / total_time) * 100

                        composition_data.append({
                            'num_agents': n,
                            'malicious_ratio': mal_ratio,
                            'type': llm_type,
                            'pct_llm': pct_llm,
                            'pct_consensus': pct_consensus,
                            'pct_network': pct_network
                        })

    df_comp = pd.DataFrame(composition_data)

    # 调整配色（降低饱和度）
    colors = {
        'llm': '#d6604d',      # 红色 - 降低饱和度
        'consensus': '#7ba3de', # 蓝色 - 降低饱和度
        'network': '#63a775'    # 绿色 - 降低饱和度
    }

    # 创建图表 - 使用折线图+误差条（上下布局）
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))

    # 子图1：诚实节点 - 折线图+误差条
    df_honest = df_comp[(df_comp['malicious_ratio'] == 0.0)]
    stats_honest = df_honest.groupby('num_agents').agg({
        'pct_llm': ['mean', 'std'],
        'pct_consensus': ['mean', 'std'],
        'pct_network': ['mean', 'std']
    }).reset_index()
    stats_honest.columns = ['num_agents', 'llm_mean', 'llm_std', 'cons_mean', 'cons_std', 'net_mean', 'net_std']
    stats_honest = stats_honest.sort_values('num_agents')

    x1 = stats_honest['num_agents'].values

    ax1.errorbar(x1, stats_honest['llm_mean'], yerr=stats_honest['llm_std'],
                 marker='o', linewidth=2.5, markersize=8, capsize=4, capthick=2,
                 color=colors['llm'], label='LLM Inference', alpha=0.8)
    ax1.errorbar(x1, stats_honest['cons_mean'], yerr=stats_honest['cons_std'],
                 marker='s', linewidth=2.5, markersize=8, capsize=4, capthick=2,
                 color=colors['consensus'], label='Consensus Protocol', alpha=0.8)
    ax1.errorbar(x1, stats_honest['net_mean'], yerr=stats_honest['net_std'],
                 marker='^', linewidth=2.5, markersize=8, capsize=4, capthick=2,
                 color=colors['network'], label='Network & Others', alpha=0.8)

    ax1.set_xlabel('Number of Agents ($n$)', fontweight='bold')
    ax1.set_ylabel('Percentage (%)', fontweight='bold')
    ax1.set_title('(a) Honest Nodes (0% Malicious)', fontweight='bold')
    ax1.set_xticks([4, 7, 10, 20])
    ax1.legend(frameon=True, shadow=True, loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.set_ylim(0, 100)

    # 子图2：恶意节点 - 折线图+误差条
    df_malicious = df_comp[(df_comp['malicious_ratio'] == 0.14)]
    stats_malicious = df_malicious.groupby('num_agents').agg({
        'pct_llm': ['mean', 'std'],
        'pct_consensus': ['mean', 'std'],
        'pct_network': ['mean', 'std']
    }).reset_index()
    stats_malicious.columns = ['num_agents', 'llm_mean', 'llm_std', 'cons_mean', 'cons_std', 'net_mean', 'net_std']
    stats_malicious = stats_malicious.sort_values('num_agents')

    x2 = stats_malicious['num_agents'].values

    ax2.errorbar(x2, stats_malicious['llm_mean'], yerr=stats_malicious['llm_std'],
                 marker='o', linewidth=2.5, markersize=8, capsize=4, capthick=2,
                 color=colors['llm'], label='LLM Inference', alpha=0.8)
    ax2.errorbar(x2, stats_malicious['cons_mean'], yerr=stats_malicious['cons_std'],
                 marker='s', linewidth=2.5, markersize=8, capsize=4, capthick=2,
                 color=colors['consensus'], label='Consensus Protocol', alpha=0.8)
    ax2.errorbar(x2, stats_malicious['net_mean'], yerr=stats_malicious['net_std'],
                 marker='^', linewidth=2.5, markersize=8, capsize=4, capthick=2,
                 color=colors['network'], label='Network & Others', alpha=0.8)

    ax2.set_xlabel('Number of Agents ($n$)', fontweight='bold')
    ax2.set_ylabel('Percentage (%)', fontweight='bold')
    ax2.set_title('(b) Malicious Nodes (14% Malicious)', fontweight='bold')
    ax2.set_xticks([4, 7, 10, 20])
    ax2.legend(frameon=True, shadow=True, loc='upper right')
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.set_ylim(0, 100)

    # 去掉总标题，保留子标题
    plt.tight_layout()

    output_path = output_dir / 'latency_pie_chart.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] 已保存: {output_path.name}")
except Exception as e:
    print(f"  [ERROR] 错误: {e}")
    import traceback
    traceback.print_exc()

# 4. 生成统计对比表
print("\n[4/4] 生成统计对比表...")
try:
    summary = df_all.groupby(['type', 'num_agents', 'malicious_ratio'])['total_latency'].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('count', 'count')
    ]).reset_index()

    # 格式化数值
    summary['mean'] = summary['mean'].round(3)
    summary['std'] = summary['std'].round(3)
    summary['min'] = summary['min'].round(3)
    summary['max'] = summary['max'].round(3)

    output_path = output_dir / 'comparison_summary.csv'
    summary.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"  [OK] 已保存: {output_path.name}")

    # 同时输出到控制台
    print("\n" + "="*70)
    print("统计摘要 (部分预览):")
    print("="*70)
    print(summary.head(10).to_string(index=False))
    print("="*70)

except Exception as e:
    print(f"  [ERROR] 错误: {e}")

# 生成完成提示
print("\n" + "="*70)
print("[OK] 所有图表和统计表已生成完成!")
print(f"[OK] 输出目录: {output_dir.absolute()}")
print("="*70)
print("\n生成的文件:")
for f in sorted(output_dir.glob('*')):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
print("="*70)
