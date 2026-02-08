"""
增强版BFT4Agent共识协议 - 集成延迟测量功能

核心改进:
1. 继承原有BFT4Agent功能
2. 添加延迟跟踪器,记录每个阶段的详细延迟
3. 模拟并行场景:为每个消息计算基于网络延迟的到达时间
4. 返回详细的延迟分析数据
"""

import sys
import os
import time
import random
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# 使用导入辅助模块
from ex.utils import import_helper

BFT4Agent = import_helper.BFT4Agent
PrePrepareMessage = import_helper.consensus.PrePrepareMessage
PrepareMessage = import_helper.consensus.PrepareMessage
CommitMessage = import_helper.consensus.CommitMessage
Replica = import_helper.consensus.Replica
ReplicaState = import_helper.consensus.ReplicaState

from ex.experiments.latency.tracker import LatencyTracker, calculate_quorum_arrival_time


class LatencyAwareNetwork:
    """
    延迟感知网络模拟器

    关键功能:
    1. 为每条消息计算到达时间(发送时间 + 网络延迟)
    2. 模拟并行执行中的消息到达顺序
    3. 返回消息的实际到达时间供延迟计算使用
    """

    def __init__(self, delay_range: tuple, packet_loss: float = 0.01):
        """
        初始化网络

        Args:
            delay_range: 延迟范围(毫秒) (min, max)
            packet_loss: 丢包率
        """
        self.delay_range = delay_range
        self.packet_loss = packet_loss
        self.nodes = {}

        # 统计信息
        self.message_count = 0
        self.drop_count = 0

    def register(self, node):
        """注册节点"""
        self.nodes[node.id] = node

    def simulate_broadcast_arrival(self, sender_id: str, message: Dict,
                                   target_ids: List[str] = None) -> List[Tuple[str, float]]:
        """
        模拟广播消息的到达时间

        关键: 为每个接收者计算一个独立的到达时间(发送时间 + 网络延迟)
        这模拟了并行场景中消息在不同时间到达不同节点

        Args:
            sender_id: 发送者ID
            message: 消息内容
            target_ids: 目标节点ID列表(None表示广播给所有)

        Returns:
            [(receiver_id, arrival_time), ...] 接收者及其消息到达时间列表
        """
        self.message_count += 1

        if target_ids is None:
            target_ids = [nid for nid in self.nodes.keys() if nid != sender_id]

        arrival_times = []

        for receiver_id in target_ids:
            # 模拟丢包
            if random.random() < self.packet_loss:
                self.drop_count += 1
                continue

            # 计算网络延迟(毫秒转秒)
            delay_ms = random.uniform(*self.delay_range)
            delay_sec = delay_ms / 1000.0

            # 到达时间 = 当前时间 + 网络延迟
            # 注意:这里使用time.time()作为发送时间的基准
            arrival_time = time.time() + delay_sec

            arrival_times.append((receiver_id, arrival_time))

            # 将消息添加到接收者的队列(实际执行会在后面)
            if receiver_id in self.nodes:
                node = self.nodes[receiver_id]
                node.receive_message(message)

        return arrival_times

    def get_delay_ms(self) -> float:
        """获取一个随机延迟值(毫秒)"""
        return random.uniform(*self.delay_range)


class BFT4AgentWithLatency(BFT4Agent):
    """
    增强版BFT4Agent - 集成延迟测量

    继承原有BFT4Agent,添加延迟记录功能
    """

    def __init__(self, *args, **kwargs):
        """
        初始化

        额外参数:
            enable_latency_tracking: 是否启用延迟跟踪(默认True)
            latency_output_dir: 延迟数据输出目录(可选)
        """
        self.enable_latency_tracking = kwargs.pop('enable_latency_tracking', True)
        self.latency_output_dir = kwargs.pop('latency_output_dir', None)

        super().__init__(*args, **kwargs)

        # 初始化延迟跟踪器
        if self.enable_latency_tracking:
            self.latency_tracker = LatencyTracker()
        else:
            self.latency_tracker = None

        # 替换为延迟感知网络(如果原网络不是)
        if hasattr(self.network, 'delay_range'):
            self.latency_aware_network = LatencyAwareNetwork(
                delay_range=self.network.delay_range,
                packet_loss=self.network.packet_loss
            )
        else:
            # 如果原网络没有delay_range,使用默认值
            self.latency_aware_network = LatencyAwareNetwork(
                delay_range=(10, 100),
                packet_loss=0.01
            )

    def run(self, task: Dict) -> Dict:
        """
        运行完整的PBFT共识流程(增强版 - 带延迟测量)

        返回的result中包含详细的延迟信息
        """
        if not self.enable_latency_tracking:
            # 如果未启用延迟跟踪,使用原始方法
            return super().run(task)

        start_time = time.time()
        view_changes = 0
        message_count = 0
        phases_completed = []

        print(f"\n{'='*60}")
        print(f"  开始BFT4Agent共识(带延迟测量) - {task['content']}")
        print(f"  节点数: {self.total_nodes}, 容错数: f={self.f}")
        print(f"  网络延迟范围: {self.latency_aware_network.delay_range}ms")
        print(f"{'='*60}")

        # 开始新一轮延迟跟踪
        self.latency_tracker.start_round(
            task=task,
            view=view_changes,
            primary_id=self._get_primary_id(view_changes),
            sequence_number=0,  # 会在后面更新
            num_agents=self.total_nodes,
            malicious_ratio=0.0,  # TODO: 从外部传入
            network_delay_range=self.latency_aware_network.delay_range
        )

        # 尝试达成共识
        for attempt in range(self.max_retries):
            self.current_view = view_changes
            primary_id = self._get_primary_id(self.current_view)

            print(f"\n[视图 {self.current_view}] 主节点: {primary_id}")

            try:
                # 重置状态
                self._reset_all_states()
                for replica in self.replicas.values():
                    replica.message_log.clear()

                # === PHASE 1: PRE-PREPARE ===
                print(f"\n[阶段1] PRE-PREPARE - Leader生成提案")
                pre_prepare_result = self._pre_prepare_phase_with_latency(
                    primary_id, task
                )
                if not pre_prepare_result['success']:
                    raise Exception("PRE-PREPARE阶段失败")

                pre_prepare_msg = pre_prepare_result['message']
                pre_prepare_latency_data = pre_prepare_result['latency_data']

                phases_completed.append("pre-prepare")
                message_count += self.total_nodes

                # === PHASE 2: PREPARE ===
                print(f"\n[阶段2] PREPARE - Backup节点评价提案")
                prepare_result = self._prepare_phase_with_latency(
                    pre_prepare_msg
                )
                if not prepare_result['success']:
                    raise Exception("PREPARE阶段超时或未达到法定人数")

                prepare_latency_data = prepare_result['latency_data']

                phases_completed.append("prepare")
                message_count += self.total_nodes * self.total_nodes

                # 检查PREPARE决策
                if prepare_result['decision'] == "N":
                    print(f"\n[PREPARE] 达成N共识,触发视图切换")
                    raise Exception(f"Proposal被拒绝")

                # === PHASE 3: COMMIT ===
                print(f"\n[阶段3] COMMIT - 对Y/N达成最终共识")
                commit_result = self._commit_phase_with_latency(
                    pre_prepare_msg, prepare_result['decision']
                )
                if not commit_result['success']:
                    raise Exception("COMMIT阶段超时或未达到法定人数")

                commit_latency_data = commit_result['latency_data']

                phases_completed.append("commit")
                message_count += self.total_nodes * self.total_nodes

                # 检查COMMIT决策
                if commit_result['decision'] == "N":
                    print(f"\n[COMMIT] 达成N共识,触发视图切换")
                    raise Exception(f"Proposal被拒绝")

                # === 成功:记录延迟并返回 ===
                self.consensus_count += 1
                total_time = time.time() - start_time

                result = {
                    "success": True,
                    "answer": pre_prepare_msg.proposal.get("answer"),
                    "view_changes": view_changes,
                    "total_messages": message_count,
                    "total_time": total_time,
                    "proposal": pre_prepare_msg.proposal,
                    "phases": phases_completed,
                    "primary_id": primary_id,
                    "sequence_number": pre_prepare_msg.sequence_number,
                    "decision": commit_result['decision'],

                    # 延迟数据
                    "latency_data": {
                        "pre_prepare": pre_prepare_latency_data,
                        "prepare": prepare_latency_data,
                        "commit": commit_latency_data,
                        "total": total_time,
                    }
                }

                # 记录到跟踪器
                self.latency_tracker.finish_round(
                    success=True,
                    view_changes=view_changes,
                    final_decision=commit_result['decision'],
                    answer=pre_prepare_msg.proposal.get("answer")
                )

                print(f"\n{'='*60}")
                print(f"  [OK] BFT4Agent共识成功!")
                print(f"  共识决策: {commit_result['decision']}")
                print(f"  最终答案: {result['answer']}")
                print(f"  总耗时: {total_time:.2f}秒")
                print(f"  PRE-PREPARE延迟: {pre_prepare_latency_data['latency']:.3f}秒")
                print(f"  PREPARE延迟: {prepare_latency_data['latency']:.3f}秒")
                print(f"  COMMIT延迟: {commit_latency_data['latency']:.3f}秒")
                print(f"{'='*60}\n")

                return result

            except Exception as e:
                print(f"\n[ERROR] 视图 {self.current_view} 失败: {e}")
                view_changes += 1
                self.view_change_count += 1
                self._trigger_view_change()

                if view_changes >= self.max_retries:
                    break

        # 失败
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"  [FAIL] BFT4Agent共识失败")
        print(f"{'='*60}\n")

        # 记录失败
        if self.latency_tracker:
            self.latency_tracker.finish_round(
                success=False,
                view_changes=view_changes,
                final_decision="N",
                answer=""
            )

        return {
            "success": False,
            "answer": None,
            "view_changes": view_changes,
            "total_messages": message_count,
            "total_time": total_time,
            "error": "Max retries exceeded",
            "phases": phases_completed,
            "decision": "N",
        }

    def _pre_prepare_phase_with_latency(self, primary_id: str, task: Dict) -> Dict:
        """
        PRE-PREPARE阶段(带延迟测量)
        """
        phase_start_time = time.time()

        # 使用原有逻辑生成PRE-PREPARE消息
        primary_replica = self.replicas[primary_id]
        primary_replica.is_primary = True
        primary_replica.agent.role = "leader"

        sequence_number = self._assign_sequence_number()

        # 生成提案
        proposal = primary_replica.agent.propose(task)

        # 打印提案详细内容
        print(f"\n{'='*80}")
        print(f"[Leader提案内容] {primary_id}")
        print(f"{'='*80}")
        print(f"问题ID: {proposal.get('task_id', 'N/A')}")
        print(f"问题内容: {proposal.get('task_content', 'N/A')[:100]}...")
        print(f"Leader答案: {proposal.get('answer', 'N/A')}")
        print(f"推理过程:")
        reasoning = proposal.get('reasoning', [])
        if isinstance(reasoning, list):
            for i, step in enumerate(reasoning, 1):
                print(f"  {i}. {step}")
        else:
            print(f"  {reasoning}")
        print(f"置信度: {proposal.get('confidence', 'N/A')}")
        print(f"{'='*80}\n")

        # 创建PRE-PREPARE消息
        pre_prepare_msg = PrePrepareMessage(
            view=self.current_view,
            sequence_number=sequence_number,
            sender_id=primary_id,
            timestamp=phase_start_time,  # 发送时间
            task=task,
            proposal=proposal,
        )

        # 记录到日志
        primary_replica.message_log.add_pre_prepare(pre_prepare_msg)
        primary_replica.state = ReplicaState.PRE_PREPARED

        # 模拟广播并记录到达时间
        broadcast_times = self.latency_aware_network.simulate_broadcast_arrival(
            sender_id=primary_id,
            message={"type": "PRE-PREPARE", "data": pre_prepare_msg},
            target_ids=[rid for rid in self.replicas.keys() if rid != primary_id]
        )

        # 记录每个节点的消息到达时间
        for receiver_id, arrival_time in broadcast_times:
            self.latency_tracker.record_message(
                message_type="PRE-PREPARE",
                sender_id=primary_id,
                receiver_id=receiver_id,
                send_time=phase_start_time,
                arrival_time=arrival_time,
                sequence_number=sequence_number
            )

        # 计算阶段延迟:最后一个消息到达的时间
        phase_end_time = max([at for _, at in broadcast_times]) if broadcast_times else time.time()
        phase_latency = phase_end_time - phase_start_time

        # 记录阶段延迟
        self.latency_tracker.record_pre_prepare_phase(
            start_time=phase_start_time,
            end_time=phase_end_time,
            quorum_reached=True,  # PRE-PREPARE总是成功(Leader广播给所有)
            quorum_size=1  # 只有Leader
        )

        return {
            "success": True,
            "message": pre_prepare_msg,
            "latency_data": {
                "latency": phase_latency,
                "start_time": phase_start_time,
                "end_time": phase_end_time,
                "quorum_reached": True,
            }
        }

    def _prepare_phase_with_latency(self, pre_prepare_msg: PrePrepareMessage) -> Dict:
        """
        PREPARE阶段(带延迟测量)
        """
        phase_start_time = time.time()
        digest = pre_prepare_msg.digest
        sequence_number = pre_prepare_msg.sequence_number
        primary_id = pre_prepare_msg.sender_id

        # 收集所有PREPARE消息及其到达时间
        prepare_messages = []
        threads = []

        # Backup节点生成PREPARE消息
        for replica_id, replica in self.replicas.items():
            if replica_id == primary_id:
                continue  # Leader不参与PREPARE

            thread = threading.Thread(
                target=self._replica_prepare_phase_with_latency,
                args=(replica, pre_prepare_msg, prepare_messages, phase_start_time)
            )
            threads.append(thread)
            thread.start()

        # 等待所有节点完成
        completed_threads = 0
        for thread in threads:
            thread.join(timeout=self.timeout)
            if not thread.is_alive():
                completed_threads += 1

        # 额外等待收集延迟消息
        if completed_threads < len(threads):
            time.sleep(min(5.0, self.timeout))

        # 分发PREPARE消息到所有副本
        for prep_msg in prepare_messages:
            for replica in self.replicas.values():
                replica.message_log.add_prepare(prep_msg)

        time.sleep(0.5)

        # 统计投票
        y_count = sum(1 for pm in prepare_messages if pm.decision == "Y")
        n_count = sum(1 for pm in prepare_messages if pm.decision == "N")

        print(f"[PREPARE] 投票统计: Y={y_count}, N={n_count}")

        # 检查是否达到法定人数
        quorum_size = self.quorum_size
        consensus_decision = ""

        if y_count >= quorum_size:
            consensus_decision = "Y"
            print(f"[PREPARE] 达到Y法定人数 ({y_count} >= {quorum_size})")
        elif n_count >= (self.f + 1):
            consensus_decision = "N"
            print(f"[PREPARE] 达到N阈值 ({n_count} >= {self.f + 1})")
            # 返回成功(达成了"拒绝"共识)
            phase_end_time = time.time()
            self.latency_tracker.record_prepare_phase(
                start_time=phase_start_time,
                end_time=phase_end_time,
                quorum_reached=True,
                messages_count=len(prepare_messages),
                quorum_size=quorum_size,
                y_count=y_count,
                n_count=n_count
            )
            return {
                "success": True,
                "decision": consensus_decision,
                "latency_data": {
                    "latency": phase_end_time - phase_start_time,
                    "start_time": phase_start_time,
                    "end_time": phase_end_time,
                    "quorum_reached": True,
                    "y_count": y_count,
                    "n_count": n_count,
                }
            }
        else:
            print(f"[PREPARE] 未达成共识 (Y={y_count}, N={n_count})")
            return {
                "success": False,
                "decision": "",
                "latency_data": {}
            }

        # 计算阶段延迟:基于最后一个达到法定人数的消息到达时间
        # 提取所有Y消息的到达时间
        y_arrival_times = [
            pm.arrival_time for pm in prepare_messages if pm.decision == "Y"
        ]
        y_arrival_times.sort()

        if len(y_arrival_times) >= quorum_size:
            # 第quorum_size个Y消息的到达时间
            quorum_arrival_time = y_arrival_times[quorum_size - 1]
        else:
            quorum_arrival_time = time.time()

        phase_latency = quorum_arrival_time - phase_start_time

        # 记录阶段延迟
        self.latency_tracker.record_prepare_phase(
            start_time=phase_start_time,
            end_time=quorum_arrival_time,
            quorum_reached=True,
            messages_count=len(prepare_messages),
            quorum_size=quorum_size,
            y_count=y_count,
            n_count=n_count
        )

        return {
            "success": True,
            "decision": consensus_decision,
            "latency_data": {
                "latency": phase_latency,
                "start_time": phase_start_time,
                "end_time": quorum_arrival_time,
                "quorum_reached": True,
                "y_count": y_count,
                "n_count": n_count,
            }
        }

    def _replica_prepare_phase_with_latency(self, replica: Replica,
                                           pre_prepare_msg: PrePrepareMessage,
                                           prepare_messages: list,
                                           phase_start_time: float):
        """单个副本的PREPARE阶段逻辑(带延迟)"""
        # 记录PRE-PREPARE消息
        replica.message_log.add_pre_prepare(pre_prepare_msg)
        replica.state = ReplicaState.PRE_PREPARED

        # 调用agent的validate方法
        proposal = pre_prepare_msg.proposal
        print(f"[{replica.agent.id}] 正在评价proposal...")

        vote = replica.agent.validate(proposal)
        decision = vote.get("decision", "N")

        print(f"[{replica.agent.id}] 评价结果: {decision}")

        # 模拟消息到达时间:发送时间 + 网络延迟
        # 注意:由于所有节点使用同一个LLM顺次执行,这里的"发送时间"需要模拟
        # 假设每个节点的处理时间大致相同,网络延迟随机
        processing_delay = random.uniform(0.01, 0.05)  # 模拟处理延迟
        network_delay_ms = self.latency_aware_network.get_delay_ms()
        network_delay_sec = network_delay_ms / 1000.0

        # 到达时间 = 阶段开始时间 + 处理延迟 + 网络延迟
        arrival_time = phase_start_time + processing_delay + network_delay_sec

        # 创建PREPARE消息
        prepare_msg = PrepareMessage(
            view=self.current_view,
            sequence_number=pre_prepare_msg.sequence_number,
            sender_id=replica.agent.id,
            timestamp=phase_start_time + processing_delay,
            digest=pre_prepare_msg.digest,
            decision=decision,
            confidence=vote.get("confidence", 0.0),
            reason=vote.get("reason", ""),
        )

        # 添加到达时间字段(用于延迟计算)
        prepare_msg.arrival_time = arrival_time

        # 记录到日志
        replica.message_log.add_prepare(prepare_msg)

        # 添加到消息列表
        prepare_messages.append(prepare_msg)

        # 记录到跟踪器
        self.latency_tracker.record_message(
            message_type="PREPARE",
            sender_id=replica.agent.id,
            receiver_id="",  # 广播
            send_time=phase_start_time + processing_delay,
            arrival_time=arrival_time,
            sequence_number=pre_prepare_msg.sequence_number,
            decision=decision
        )

    def _commit_phase_with_latency(self, pre_prepare_msg: PrePrepareMessage,
                                   prepare_decision: str) -> Dict:
        """
        COMMIT阶段(带延迟测量)
        """
        phase_start_time = time.time()
        digest = pre_prepare_msg.digest
        sequence_number = pre_prepare_msg.sequence_number

        # 收集所有COMMIT消息
        commit_messages = []
        threads = []

        # 所有节点发送COMMIT消息
        for replica_id, replica in self.replicas.items():
            thread = threading.Thread(
                target=self._replica_commit_phase_with_latency,
                args=(replica, pre_prepare_msg, commit_messages, prepare_decision, phase_start_time)
            )
            threads.append(thread)
            thread.start()

        # 等待所有节点完成
        completed_threads = 0
        for thread in threads:
            thread.join(timeout=self.timeout)
            if not thread.is_alive():
                completed_threads += 1

        # 额外等待
        if completed_threads < len(threads):
            time.sleep(min(5.0, self.timeout))

        # 分发COMMIT消息
        for commit_msg in commit_messages:
            for replica in self.replicas.values():
                replica.message_log.add_commit(commit_msg)

        time.sleep(0.5)

        # 统计投票
        y_count = sum(1 for cm in commit_messages if cm.decision == "Y")
        n_count = sum(1 for cm in commit_messages if cm.decision == "N")

        print(f"[COMMIT] 投票统计: Y={y_count}, N={n_count}")

        # 检查是否达到法定人数
        quorum_size = self.quorum_size
        final_decision = ""

        if y_count >= quorum_size:
            final_decision = "Y"
            print(f"[COMMIT] 达到Y法定人数 ({y_count} >= {quorum_size})")
        elif n_count >= (self.f + 1):
            final_decision = "N"
            print(f"[COMMIT] 达到N阈值 ({n_count} >= {self.f + 1})")

            # 计算阶段延迟
            n_arrival_times = [
                cm.arrival_time for cm in commit_messages if cm.decision == "N"
            ]
            n_arrival_times.sort()
            quorum_arrival_time = n_arrival_times[self.f] if len(n_arrival_times) > self.f else time.time()

            self.latency_tracker.record_commit_phase(
                start_time=phase_start_time,
                end_time=quorum_arrival_time,
                quorum_reached=True,
                messages_count=len(commit_messages),
                quorum_size=quorum_size,
                y_count=y_count,
                n_count=n_count
            )

            return {
                "success": True,
                "decision": final_decision,
                "latency_data": {
                    "latency": quorum_arrival_time - phase_start_time,
                    "start_time": phase_start_time,
                    "end_time": quorum_arrival_time,
                    "quorum_reached": True,
                    "y_count": y_count,
                    "n_count": n_count,
                }
            }
        else:
            print(f"[COMMIT] 未达成共识 (Y={y_count}, N={n_count})")
            return {
                "success": False,
                "decision": "",
                "latency_data": {}
            }

        # 计算阶段延迟(基于Y消息)
        y_arrival_times = [
            cm.arrival_time for cm in commit_messages if cm.decision == "Y"
        ]
        y_arrival_times.sort()

        if len(y_arrival_times) >= quorum_size:
            quorum_arrival_time = y_arrival_times[quorum_size - 1]
        else:
            quorum_arrival_time = time.time()

        phase_latency = quorum_arrival_time - phase_start_time

        # 记录阶段延迟
        self.latency_tracker.record_commit_phase(
            start_time=phase_start_time,
            end_time=quorum_arrival_time,
            quorum_reached=True,
            messages_count=len(commit_messages),
            quorum_size=quorum_size,
            y_count=y_count,
            n_count=n_count
        )

        return {
            "success": True,
            "decision": final_decision,
            "latency_data": {
                "latency": phase_latency,
                "start_time": phase_start_time,
                "end_time": quorum_arrival_time,
                "quorum_reached": True,
                "y_count": y_count,
                "n_count": n_count,
            }
        }

    def _replica_commit_phase_with_latency(self, replica: Replica,
                                          pre_prepare_msg: PrePrepareMessage,
                                          commit_messages: list,
                                          prepare_decision: str,
                                          phase_start_time: float):
        """单个副本的COMMIT阶段逻辑(带延迟)"""
        digest = pre_prepare_msg.digest
        sequence_number = pre_prepare_msg.sequence_number

        # 使用PREPARE阶段的共识决策
        decision = prepare_decision

        # 模拟消息到达时间
        processing_delay = random.uniform(0.01, 0.05)
        network_delay_ms = self.latency_aware_network.get_delay_ms()
        network_delay_sec = network_delay_ms / 1000.0

        arrival_time = phase_start_time + processing_delay + network_delay_sec

        # 创建COMMIT消息
        commit_msg = CommitMessage(
            view=self.current_view,
            sequence_number=sequence_number,
            sender_id=replica.agent.id,
            timestamp=phase_start_time + processing_delay,
            digest=digest,
            decision=decision,
        )

        # 添加到达时间字段
        commit_msg.arrival_time = arrival_time

        # 记录到日志
        replica.message_log.add_commit(commit_msg)

        # 添加到消息列表
        commit_messages.append(commit_msg)

        # 记录到跟踪器
        self.latency_tracker.record_message(
            message_type="COMMIT",
            sender_id=replica.agent.id,
            receiver_id="",
            send_time=phase_start_time + processing_delay,
            arrival_time=arrival_time,
            sequence_number=sequence_number,
            decision=decision
        )

    def get_latency_summary(self) -> Dict:
        """获取延迟统计摘要"""
        if self.latency_tracker:
            return self.latency_tracker.get_summary()
        return {}
