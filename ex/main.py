"""
BFT4Agent 实验统一入口

支持多种实验类型：
- latency: 端到端延迟测试
- malicious_vs_latency: 恶意节点比例与延迟关系测试
- fault_tolerance: 容错边界测试（新）
- accuracy: 准确率测试（待实现）
- scalability: 可扩展性测试（待实现）
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 使用导入辅助模块
from ex.utils import import_helper

# 导入实验模块
from ex.experiments.latency import LatencyExperiment
from ex.experiments.malicious_vs_latency import MaliciousVsLatencyExperiment
from ex.experiments.fault_tolerance import FaultToleranceExperiment


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='BFT4Agent实验系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行延迟实验（快速测试）
  python ex/main.py latency --quick-test

  # 运行延迟实验（完整）
  python ex/main.py latency --config ex/configs/latency.yaml

  # 运行恶意节点比例实验（快速测试）
  python ex/main.py malicious_vs_latency --quick-test

  # 运行恶意节点比例实验（完整）
  python ex/main.py malicious_vs_latency --config ex/configs/malicious_vs_latency.yaml

  # 运行容错边界实验（快速测试）
  python ex/main.py fault_tolerance --quick-test

  # 运行容错边界实验（完整，使用真实LLM）
  python ex/main.py fault_tolerance --config ex/configs/fault_tolerance.yaml

  # 分析已有结果
  python ex/main.py latency --analyze ex/results/data/experiment_20250128.json
        """
    )

    parser.add_argument(
        'experiment_type',
        type=str,
        choices=['latency', 'malicious_vs_latency', 'fault_tolerance', 'accuracy', 'scalability'],
        help='实验类型'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径（默认根据实验类型自动选择）'
    )

    parser.add_argument(
        '--quick-test',
        action='store_true',
        help='快速测试模式'
    )

    parser.add_argument(
        '--analyze',
        type=str,
        help='分析已有结果文件'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='ex/results',
        help='结果输出目录'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print(f"\n{'='*70}")
    print(f"  BFT4Agent 实验系统")
    print(f"  实验类型: {args.experiment_type}")
    print(f"{'='*70}\n")

    # 根据实验类型创建实验实例
    if args.experiment_type == 'latency':
        config_file = args.config if args.config else 'ex/configs/latency.yaml'
        experiment = LatencyExperiment(
            config_file=config_file,
            output_dir=args.output_dir
        )

        if args.analyze:
            # 分析已有结果
            print(f"正在分析结果文件: {args.analyze}")
            experiment.analyze_results(args.analyze)
        else:
            # 运行实验
            if args.quick_test:
                print("运行快速测试模式...")
                experiment.run_quick_test()
            else:
                print("运行完整实验...")
                experiment.run()

    elif args.experiment_type == 'malicious_vs_latency':
        config_file = args.config if args.config else 'ex/configs/malicious_vs_latency.yaml'
        experiment = MaliciousVsLatencyExperiment(
            config_file=config_file,
            output_dir=args.output_dir
        )

        if args.analyze:
            # 分析已有结果
            print(f"正在分析结果文件: {args.analyze}")
            experiment.analyze_results(args.analyze)
        else:
            # 运行实验
            if args.quick_test:
                print("运行快速测试模式...")
                experiment.run_quick_test()
            else:
                print("运行完整实验...")
                experiment.run()

    elif args.experiment_type == 'fault_tolerance':
        config_file = args.config if args.config else 'ex/configs/fault_tolerance.yaml'
        experiment = FaultToleranceExperiment(
            config_file=config_file,
            output_dir=args.output_dir
        )

        if args.analyze:
            # 分析已有结果
            print(f"正在分析结果文件: {args.analyze}")
            experiment.analyze_results(args.analyze)
        else:
            # 运行实验
            if args.quick_test:
                print("运行快速测试模式...")
                experiment.run_quick_test()
            else:
                print("运行完整实验...")
                experiment.run()

    elif args.experiment_type == 'accuracy':
        print("准确率实验尚未实现")
        sys.exit(1)

    elif args.experiment_type == 'scalability':
        print("可扩展性实验尚未实现")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  完成!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
