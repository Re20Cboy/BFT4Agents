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
    plt.figure(figsize=(7, 5))

    # 使用errorbar='sd'可能在新版seaborn中有问题，改用ci='sd'
    sns.lineplot(data=df_all[df_all['malicious_ratio'] == 0.0],
                 x='num_agents', y='total_latency', hue='type', style='type',
                 markers=True, dashes=False, palette='Set1',
                 errorbar='sd', err_style='band', alpha=0.7)

    plt.xlabel('Number of Agents ($n$)', fontweight='bold')
    plt.ylabel('Total Latency (seconds)', fontweight='bold')
    plt.title('Impact of LLM Inference on End-to-End Latency', fontweight='bold')
    plt.legend(title='Experiment Setup', frameon=True, shadow=True)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.grid(True, linestyle='--', alpha=0.3)

    output_path = output_dir / 'comparison_llm_vs_baseline.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] 已保存: {output_path.name}")
except Exception as e:
    print(f"  [ERROR] 错误: {e}")

# 2. 对数坐标系下的可扩展性分析 (Scalability in Log Scale)
print("\n[2/4] 生成对数坐标系可扩展性分析...")
try:
    plt.figure(figsize=(7, 5))
    sns.lineplot(data=df_all, x='num_agents', y='total_latency', hue='type',
                 style='malicious_ratio', markers=True, palette='Set1',
                 alpha=0.8, linewidth=2)
    plt.yscale('log')
    plt.xlabel('Number of Agents ($n$)', fontweight='bold')
    plt.ylabel('Total Latency (seconds, Log Scale)', fontweight='bold')
    plt.title('Scalability Analysis (Log Scale)', fontweight='bold')
    plt.legend(title='Type & Malicious Ratio', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3, which='both')

    output_path = output_dir / 'scalability_log_plot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] 已保存: {output_path.name}")
except Exception as e:
    print(f"  [ERROR] 错误: {e}")

# 3. 延迟占比饼图 (Latency Breakdown Pie Chart)
print("\n[3/4] 生成延迟占比饼图...")
try:
    # 选取 n=20, malicious_ratio=0.0 的情况
    df_20 = df_llm[(df_llm['num_agents'] == 20) & (df_llm['malicious_ratio'] == 0.0)].mean(numeric_only=True)
    df_20_base = df_base[(df_base['num_agents'] == 20) & (df_base['malicious_ratio'] == 0.0)].mean(numeric_only=True)

    # 计算 LLM 纯推理延迟 (假设是 pre_prepare 的增量)
    llm_inference = df_20['pre_prepare'] - df_20_base['pre_prepare']
    consensus_overhead = df_20['prepare'] + df_20['commit']
    other_overhead = df_20['total_latency'] - llm_inference - consensus_overhead

    plt.figure(figsize=(6, 6))
    labels = ['LLM Inference', 'Consensus Protocol', 'Network & Others']
    sizes = [llm_inference, consensus_overhead, other_overhead]
    colors = ['#ff6b6b', '#4ecdc4', '#95e1d3']
    explode = (0.1, 0, 0)

    wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%',
                                         startangle=140, colors=colors,
                                         explode=explode, shadow=True,
                                         textprops={'fontweight': 'bold'})

    # 美化百分比文本
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')

    plt.title('Latency Composition (n=20, w/ LLM)', fontweight='bold', pad=20)

    output_path = output_dir / 'latency_pie_chart.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] 已保存: {output_path.name}")
except Exception as e:
    print(f"  [ERROR] 错误: {e}")

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
