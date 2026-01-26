"""
简化的P2Pnetwork模拟
"""

import time
import random
from typing import Dict, List, Callable


class Network:
    """简化的P2Pnetwork模拟器"""

    def __init__(
        self,
        delay_range: tuple = (10, 100),  # (min, max) in ms
        packet_loss: float = 0.01,
    ):
        """
        initnetwork

        Args:
            delay_range: delay范围（毫秒）
            packet_loss: 丢包率 (0.0-1.0)
        """
        self.delay_range = delay_range
        self.packet_loss = packet_loss
        self.nodes: Dict[str, object] = {}

        # stats
        self.message_count = 0
        self.drop_count = 0

    def register(self, node):
        """registernode"""
        self.nodes[node.id] = node
        print(f"[Network] node {node.id} 已register")

    def unregister(self, node_id: str):
        """注销node"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            print(f"[Network] node {node_id} 已注销")

    def broadcast(
        self,
        message: Dict,
        sender_id: str,
        target_ids: List[str] = None,
    ) -> Dict[str, bool]:
        """
        broadcast消息

        Args:
            message: 消息内容
            sender_id: 发送者ID
            target_ids: 目标nodeID列表（None表示broadcast给所有）

        Returns:
            deliverresult字典 {node_id: success}
        """
        self.message_count += 1

        # 确定接收者
        if target_ids is None:
            target_ids = [nid for nid in self.nodes.keys() if nid != sender_id]

        results = {}

        for node_id in target_ids:
            # 模拟丢包
            if random.random() < self.packet_loss:
                self.drop_count += 1
                results[node_id] = False
                continue

            # 模拟delay
            delay_ms = random.uniform(*self.delay_range)
            time.sleep(delay_ms / 1000.0)  # 转换为秒

            # deliver消息
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.receive_message(message)
                results[node_id] = True
            else:
                results[node_id] = False

        return results

    def send(self, message: Dict, sender_id: str, receiver_id: str) -> bool:
        """
        单播消息

        Args:
            message: 消息内容
            sender_id: 发送者ID
            receiver_id: 接收者ID

        Returns:
            是否deliversuccess
        """
        results = self.broadcast(message, sender_id, [receiver_id])
        return results.get(receiver_id, False)

    def get_stats(self) -> Dict:
        """获取networkstats信息"""
        total_sent = self.message_count
        total_dropped = self.drop_count
        success_rate = (
            (total_sent - total_dropped) / total_sent if total_sent > 0 else 1.0
        )

        return {
            "total_sent": total_sent,
            "total_dropped": total_dropped,
            "success_rate": success_rate,
            "avg_delay_ms": sum(self.delay_range) / 2,
        }

    def reset_stats(self):
        """重置stats"""
        self.message_count = 0
        self.drop_count = 0

    def __repr__(self):
        return f"Network(nodes={len(self.nodes)}, delay={self.delay_range}ms)"


if __name__ == "__main__":
    # testnetwork
    print("=== Testing Network ===")

    from agents import Agent

    # 创建network
    net = Network(delay_range=(10, 50), packet_loss=0.0)

    # 创建node
    agents = []
    for i in range(3):
        agent = Agent(f"agent_{i+1}")
        agents.append(agent)
        net.register(agent)

    print(f"\nnetwork状态: {net}")

    # testbroadcast
    print("\n=== Testing Broadcast ===")
    message = {"type": "PROPOSE", "data": "test message"}
    results = net.broadcast(message, sender_id="agent_1")

    print(f"deliverresult: {results}")

    # test单播
    print("\n=== Testing Unicast ===")
    message = {"type": "VOTE", "data": "Y"}
    success = net.send(message, sender_id="agent_2", receiver_id="agent_3")
    print(f"deliversuccess: {success}")

    # stats信息
    print("\n=== Network Stats ===")
    stats = net.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
