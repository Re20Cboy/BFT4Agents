#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
容错边界实验 - 结果可视化脚本

使用方法:
    python ex/experiments/fault_tolerance/visualize_results.py

或指定JSON文件:
    python ex/experiments/fault_tolerance/visualize_results.py --file ex/results/data/fault_tolerance_latest.json
"""

import json
import argparse
import os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


def load_results(json_path):
    """加载实验结果"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def plot_success_rate(data, output_dir):
    """图1: 成功率 vs 恶意节点比例"""
    honest_results = [r for r in data['results'] if r['config']['leader_type'] == 'honest']
    malicious_results = [r for r in data['results'] if r['config']['leader_type'] == 'malicious']

    fig, ax = plt.subplots(figsize=(10, 6))

    if honest_results:
        x_honest = [r['config']['malicious_ratio'] for r in honest_results]
        y_honest = [r['summary']['success_rate'] for r in honest_results]
        ax.plot(x_honest, y_honest, marker='o', linewidth=2.5, label='诚实Leader', color='#2ecc71')

    if malicious_results:
        x_malicious = [r['config']['malicious_ratio'] for r in malicious_results]
        y_malicious = [r['summary']['success_rate'] for r in malicious_results]
        ax.plot(x_malicious, y_malicious, marker='s', linewidth=2.5, label='恶意Leader', color='#e74c3c')

    # 理论阈值线
    ax.axvline(x=1/3, color='gray', linestyle='--', linewidth=1.5, label='理论阈值 (33%)')

    ax.set_xlabel('恶意节点比例', fontsize=12)
    ax.set_ylabel('共识成功率', fontsize=12)
    ax.set_title('BFT4Agent 容错边界测试 - 成功率分析', fontsize=14, fontweight='bold')
    ax.set_ylim([-0.05, 1.05])
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower left', fontsize=11)

    plt.tight_layout()
    output_path = f"{output_dir}/success_rate_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] 图表已保存: {output_path}")


def plot_voting_margin(data, output_dir):
    """图2: 投票余量分析"""
    honest_results = [r for r in data['results'] if r['config']['leader_type'] == 'honest']

    if not honest_results:
        print("[SKIP] 跳过投票余量分析 (无诚实Leader数据)")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = [r['config']['malicious_ratio'] for r in honest_results]
    avg_margin = [r['summary']['avg_margin'] for r in honest_results]
    min_margin = [r['summary']['min_margin'] for r in honest_results]

    ax.plot(x, avg_margin, marker='o', linewidth=2.5, label='平均余量', color='#3498db')
    ax.plot(x, min_margin, marker='s', linewidth=2.5, label='最小余量', color='#e67e22')

    # 0余量线 (危险线)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5, label='危险线 (0余量)')

    # 填充区域
    ax.fill_between(x, min_margin, avg_margin, alpha=0.2, color='#3498db')

    ax.set_xlabel('恶意节点比例', fontsize=12)
    ax.set_ylabel('距离2f+1阈值的余量 (票数)', fontsize=12)
    ax.set_title('BFT4Agent 投票安全边际分析', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)

    plt.tight_layout()
    output_path = f"{output_dir}/voting_margin_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] 图表已保存: {output_path}")


def plot_vote_distribution(data, output_dir):
    """图3: Y票/N票分布"""
    honest_results = [r for r in data['results'] if r['config']['leader_type'] == 'honest']

    if not honest_results:
        print("[SKIP] 跳过投票分布分析 (无诚实Leader数据)")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(honest_results))
    width = 0.35

    y_votes = [r['summary']['avg_y_count'] for r in honest_results]
    n_votes = [r['summary']['avg_n_count'] for r in honest_results]
    labels = [f"{r['config']['malicious_ratio']:.0%}" for r in honest_results]

    bars1 = ax.bar(x - width/2, y_votes, width, label='Y票 (支持)', color='#2ecc71', alpha=0.8)
    bars2 = ax.bar(x + width/2, n_votes, width, label='N票 (反对)', color='#e74c3c', alpha=0.8)

    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('恶意节点比例', fontsize=12)
    ax.set_ylabel('平均票数', fontsize=12)
    ax.set_title('BFT4Agent 投票分布统计', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = f"{output_dir}/vote_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] 图表已保存: {output_path}")


def plot_latency_comparison(data, output_dir):
    """图4: 延迟对比"""
    honest_results = [r for r in data['results'] if r['config']['leader_type'] == 'honest']

    if not honest_results:
        print("[SKIP] 跳过延迟分析 (无诚实Leader数据)")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = [r['config']['malicious_ratio'] for r in honest_results]
    avg_latency = [r['summary']['avg_total_latency'] for r in honest_results]

    ax.plot(x, avg_latency, marker='o', linewidth=2.5, color='#9b59b6', label='平均总延迟')

    ax.set_xlabel('恶意节点比例', fontsize=12)
    ax.set_ylabel('平均延迟 (秒)', fontsize=12)
    ax.set_title('BFT4Agent 共识延迟分析', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)

    plt.tight_layout()
    output_path = f"{output_dir}/latency_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] 图表已保存: {output_path}")


def create_summary_table(data, output_dir):
    """生成汇总表格 (Markdown格式)"""
    honest_results = [r for r in data['results'] if r['config']['leader_type'] == 'honest']

    if not honest_results:
        print("[SKIP] 跳过汇总表格生成 (无诚实Leader数据)")
        return

    lines = []
    lines.append("# 容错边界实验结果汇总")
    lines.append("")
    lines.append("## 诚实Leader场景")
    lines.append("")
    lines.append("| 恶意节点数 | 恶意比例 | 成功率 | Y/N平均投票 | 2f+1阈值 | 平均余量 | 最小余量 |")
    lines.append("|----------|---------|--------|------------|---------|---------|---------|")

    for r in honest_results:
        malicious_count = r['config']['malicious_count']
        malicious_ratio = f"{r['config']['malicious_ratio']:.1%}"
        success_rate = f"{r['summary']['success_rate']:.1%}"
        avg_votes = f"{r['summary']['avg_y_count']:.0f}/{r['summary']['avg_n_count']:.0f}"
        quorum = r['summary']['quorum_threshold']
        avg_margin = f"+{r['summary']['avg_margin']:.1f}"
        min_margin = f"+{r['summary']['min_margin']:.1f}"

        lines.append(f"| {malicious_count} | {malicious_ratio} | {success_rate} | {avg_votes} | {quorum} | {avg_margin} | {min_margin} |")

    lines.append("")
    lines.append("## 关键观察")
    lines.append("")
    lines.append(f"- 实验时间: {data['timestamp']}")
    if 'config' in data:
        config = data['config']
        num_agents = config.get('num_agents', 'N/A')
        llm_backend = config.get('llm_backend', 'N/A')
        lines.append(f"- 实验配置: {num_agents}个节点")
        lines.append(f"- LLM后端: {llm_backend}")

    output_path = f"{output_dir}/summary_table.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"[OK] 汇总表格已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='容错边界实验结果可视化')
    parser.add_argument('--file', type=str,
                        default='ex/results/data/fault_tolerance_latest.json',
                        help='实验结果JSON文件路径')
    parser.add_argument('--output', type=str,
                        default='ex/results/figures/fault_tolerance',
                        help='输出目录')

    args = parser.parse_args()

    # 加载数据
    print(f"正在加载实验结果: {args.file}")
    data = load_results(args.file)

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    print(f"输出目录: {args.output}")
    print("")

    # 生成图表
    print("生成可视化图表:")
    print("-" * 50)
    plot_success_rate(data, args.output)
    plot_voting_margin(data, args.output)
    plot_vote_distribution(data, args.output)
    plot_latency_comparison(data, args.output)
    create_summary_table(data, args.output)
    print("-" * 50)
    print(f"\n[SUCCESS] 所有图表已生成完成!")
    print(f"  位置: {args.output}/")


if __name__ == '__main__':
    main()
