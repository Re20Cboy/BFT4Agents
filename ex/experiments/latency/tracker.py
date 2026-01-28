"""
延迟跟踪器 - 用于测量BFT4Agent协议的端到端延迟

关键设计：
1. 由于代码使用同一个LLM后端顺次执行(而非并行),因此需要模拟并行场景
2. 延迟计算基于消息到达时间(而非代码运行时间)
3. 每个阶段的延迟 = 收集足够共识消息的最后一个到达时间 - 阶段开始时间
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MessageTimestamp:
    """单个消息的时间戳"""
    message_type: str  # PRE-PREPARE, PREPARE, COMMIT
    sender_id: str
    receiver_id: str  # Optional (广播消息有多个接收者)
    send_time: float  # 发送时间
    arrival_time: float  # 到达时间(包含网络延迟)
    sequence_number: int = 0
    decision: str = ""  # Y/N for PREPARE and COMMIT messages


@dataclass
class PhaseLatency:
    """单个阶段的延迟记录"""
    phase_name: str  # pre_prepare, prepare, commit, total
    start_time: float  # 阶段开始时间
    end_time: float  # 阶段结束时间(达成共识的时间)
    latency: float  # end_time - start_time
    quorum_reached: bool  # 是否达到法定人数
    messages_count: int  # 收集到的消息数量
    quorum_size: int  # 需要的法定人数


@dataclass
class RoundLatencyRecord:
    """一轮共识的完整延迟记录"""
    task_id: str
    task_content: str
    view: int
    primary_id: str
    sequence_number: int
    num_agents: int
    malicious_ratio: float
    network_delay_range: tuple

    # 各阶段延迟
    pre_prepare_phase: Optional[PhaseLatency] = None
    prepare_phase: Optional[PhaseLatency] = None
    commit_phase: Optional[PhaseLatency] = None
    total_latency: float = 0.0

    # 投票统计
    prepare_y_count: int = 0
    prepare_n_count: int = 0
    commit_y_count: int = 0
    commit_n_count: int = 0

    # 结果
    success: bool = False
    view_changes: int = 0
    final_decision: str = ""  # Y/N
    answer: str = ""

    # 消息时间戳列表(用于详细分析)
    message_timestamps: List[MessageTimestamp] = field(default_factory=list)

    # 时间戳
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class LatencyTracker:
    """
    延迟跟踪器

    功能：
    1. 记录每个消息的发送和到达时间
    2. 计算各阶段的延迟(基于最后一个达成共识的消息到达时间)
    3. 统计投票情况
    """

    def __init__(self):
        self.current_round: Optional[RoundLatencyRecord] = None
        self.round_records: List[RoundLatencyRecord] = []

    def start_round(self, task: Dict, view: int, primary_id: str,
                   sequence_number: int, num_agents: int, malicious_ratio: float,
                   network_delay_range: tuple):
        """开始一轮新的共识"""
        self.current_round = RoundLatencyRecord(
            task_id=task.get("task_id", f"task_{int(time.time())}"),
            task_content=task.get("content", ""),
            view=view,
            primary_id=primary_id,
            sequence_number=sequence_number,
            num_agents=num_agents,
            malicious_ratio=malicious_ratio,
            network_delay_range=network_delay_range,
        )

    def record_pre_prepare_phase(self, start_time: float, end_time: float,
                                 quorum_reached: bool, quorum_size: int):
        """记录PRE-PREPARE阶段"""
        latency = end_time - start_time
        self.current_round.pre_prepare_phase = PhaseLatency(
            phase_name="pre_prepare",
            start_time=start_time,
            end_time=end_time,
            latency=latency,
            quorum_reached=quorum_reached,
            messages_count=1,  # PRE-PREPARE只有1条消息(Leader广播)
            quorum_size=quorum_size
        )

    def record_prepare_phase(self, start_time: float, end_time: float,
                            quorum_reached: bool, messages_count: int,
                            quorum_size: int, y_count: int, n_count: int):
        """记录PREPARE阶段"""
        latency = end_time - start_time
        self.current_round.prepare_phase = PhaseLatency(
            phase_name="prepare",
            start_time=start_time,
            end_time=end_time,
            latency=latency,
            quorum_reached=quorum_reached,
            messages_count=messages_count,
            quorum_size=quorum_size
        )
        self.current_round.prepare_y_count = y_count
        self.current_round.prepare_n_count = n_count

    def record_commit_phase(self, start_time: float, end_time: float,
                           quorum_reached: bool, messages_count: int,
                           quorum_size: int, y_count: int, n_count: int):
        """记录COMMIT阶段"""
        latency = end_time - start_time
        self.current_round.commit_phase = PhaseLatency(
            phase_name="commit",
            start_time=start_time,
            end_time=end_time,
            latency=latency,
            quorum_reached=quorum_reached,
            messages_count=messages_count,
            quorum_size=quorum_size
        )
        self.current_round.commit_y_count = y_count
        self.current_round.commit_n_count = n_count

    def record_message(self, message_type: str, sender_id: str,
                      send_time: float, arrival_time: float,
                      sequence_number: int = 0, decision: str = "",
                      receiver_id: str = ""):
        """记录单个消息的时间戳"""
        msg_ts = MessageTimestamp(
            message_type=message_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            send_time=send_time,
            arrival_time=arrival_time,
            sequence_number=sequence_number,
            decision=decision
        )
        self.current_round.message_timestamps.append(msg_ts)

    def finish_round(self, success: bool, view_changes: int,
                    final_decision: str, answer: str):
        """完成一轮共识"""
        # 计算总延迟
        if self.current_round.pre_prepare_phase:
            total_end = self.current_round.commit_phase.end_time if self.current_round.commit_phase else 0
            total_start = self.current_round.pre_prepare_phase.start_time
            self.current_round.total_latency = total_end - total_start

        self.current_round.success = success
        self.current_round.view_changes = view_changes
        self.current_round.final_decision = final_decision
        self.current_round.answer = answer

        # 保存记录
        self.round_records.append(self.current_round)

    def get_summary(self) -> Dict:
        """获取汇总统计"""
        if not self.round_records:
            return {}

        total_rounds = len(self.round_records)
        successful_rounds = sum(1 for r in self.round_records if r.success)

        # 计算平均延迟
        successful_records = [r for r in self.round_records if r.success]

        avg_total_latency = 0
        avg_pre_prepare_latency = 0
        avg_prepare_latency = 0
        avg_commit_latency = 0

        if successful_records:
            avg_total_latency = sum(r.total_latency for r in successful_records) / len(successful_records)
            avg_pre_prepare_latency = sum(
                r.pre_prepare_phase.latency for r in successful_records
                if r.pre_prepare_phase
            ) / len([r for r in successful_records if r.pre_prepare_phase])

            avg_prepare_latency = sum(
                r.prepare_phase.latency for r in successful_records
                if r.prepare_phase
            ) / len([r for r in successful_records if r.prepare_phase])

            avg_commit_latency = sum(
                r.commit_phase.latency for r in successful_records
                if r.commit_phase
            ) / len([r for r in successful_records if r.commit_phase])

        return {
            "total_rounds": total_rounds,
            "successful_rounds": successful_rounds,
            "success_rate": successful_rounds / total_rounds if total_rounds > 0 else 0,
            "avg_total_latency": avg_total_latency,
            "avg_pre_prepare_latency": avg_pre_prepare_latency,
            "avg_prepare_latency": avg_prepare_latency,
            "avg_commit_latency": avg_commit_latency,
            "round_records": [self._round_to_dict(r) for r in self.round_records]
        }

    def _round_to_dict(self, round_record: RoundLatencyRecord) -> Dict:
        """将RoundLatencyRecord转换为字典"""
        return {
            "task_id": round_record.task_id,
            "task_content": round_record.task_content,
            "view": round_record.view,
            "primary_id": round_record.primary_id,
            "sequence_number": round_record.sequence_number,
            "num_agents": round_record.num_agents,
            "malicious_ratio": round_record.malicious_ratio,
            "network_delay_range": round_record.network_delay_range,
            "pre_prepare_phase": {
                "latency": round_record.pre_prepare_phase.latency,
                "start_time": round_record.pre_prepare_phase.start_time,
                "end_time": round_record.pre_prepare_phase.end_time,
                "quorum_reached": round_record.pre_prepare_phase.quorum_reached,
            } if round_record.pre_prepare_phase else None,
            "prepare_phase": {
                "latency": round_record.prepare_phase.latency,
                "start_time": round_record.prepare_phase.start_time,
                "end_time": round_record.prepare_phase.end_time,
                "quorum_reached": round_record.prepare_phase.quorum_reached,
                "y_count": round_record.prepare_y_count,
                "n_count": round_record.prepare_n_count,
            } if round_record.prepare_phase else None,
            "commit_phase": {
                "latency": round_record.commit_phase.latency,
                "start_time": round_record.commit_phase.start_time,
                "end_time": round_record.commit_phase.end_time,
                "quorum_reached": round_record.commit_phase.quorum_reached,
                "y_count": round_record.commit_y_count,
                "n_count": round_record.commit_n_count,
            } if round_record.commit_phase else None,
            "total_latency": round_record.total_latency,
            "success": round_record.success,
            "view_changes": round_record.view_changes,
            "final_decision": round_record.final_decision,
            "answer": round_record.answer,
            "timestamp": round_record.timestamp,
        }


def calculate_quorum_arrival_time(messages: List[MessageTimestamp],
                                  quorum_size: int, decision: str = "") -> float:
    """
    计算达到法定人数的时间

    关键逻辑：找到第quorum_size个符合条件消息的到达时间
    这模拟了并行执行中最后一个达成共识的消息到达时间

    Args:
        messages: 消息列表
        quorum_size: 需要的法定人数
        decision: 筛选条件(Y/N),空表示不筛选

    Returns:
        达到法定人数的时间(最后一个符合条件的消息的到达时间)
    """
    if decision:
        # 筛选特定决策的消息
        filtered = [m for m in messages if m.decision == decision]
    else:
        filtered = messages

    # 按到达时间排序
    sorted_messages = sorted(filtered, key=lambda x: x.arrival_time)

    if len(sorted_messages) < quorum_size:
        # 未达到法定人数
        return 0

    # 返回第quorum_size个消息的到达时间
    return sorted_messages[quorum_size - 1].arrival_time
