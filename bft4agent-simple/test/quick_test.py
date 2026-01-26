"""
Quick Test Script - Verify all modules work correctly
"""

import sys
import os


def test_imports():
    """Test imports"""
    print("[1/5] Testing module imports...")
    try:
        from config import load_config
        from agents import create_agents, Agent
        from network import Network
        from consensus import BFT4Agent
        from llm import LLMCaller
        print("[OK] All modules imported successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_config():
    """Test configuration"""
    print("\n[2/5] Testing configuration system...")
    try:
        from config import load_config

        config = load_config()
        assert "num_agents" in config
        assert "malicious_ratio" in config
        print(f"[OK] Configuration loaded: {config['num_agents']} agents")
        return True
    except Exception as e:
        print(f"[FAIL] Config test failed: {e}")
        return False


def test_agents():
    """Test Agent creation"""
    print("\n[3/5] Testing Agent creation...")
    try:
        from agents import create_agents

        agents = create_agents(num_agents=7, malicious_ratio=0.14)
        assert len(agents) == 7

        malicious_count = sum(1 for a in agents if a.is_malicious)
        assert malicious_count == 1  # 7 * 0.14 = 1

        print(f"[OK] Agents created: {len(agents)} agents, {malicious_count} malicious")
        return True
    except Exception as e:
        print(f"[FAIL] Agent test failed: {e}")
        return False


def test_network():
    """Test network"""
    print("\n[4/5] Testing network simulation...")
    try:
        from agents import Agent
        from network import Network

        net = Network()
        agent1 = Agent("agent_1")
        agent2 = Agent("agent_2")

        net.register(agent1)
        net.register(agent2)

        # Test broadcast
        message = {"type": "TEST", "data": "hello"}
        results = net.broadcast(message, sender_id="agent_1")

        assert results["agent_2"] == True
        print("[OK] Network simulation successful")
        return True
    except Exception as e:
        print(f"[FAIL] Network test failed: {e}")
        return False


def test_consensus():
    """Test consensus"""
    print("\n[5/5] Testing BFT consensus...")
    try:
        from agents import create_agents
        from network import Network
        from consensus import BFT4Agent
        from llm import LLMCaller

        # Create components
        agents = create_agents(num_agents=7, malicious_ratio=0.0)  # No malicious
        network = Network()

        for agent in agents:
            network.register(agent)

        llm = LLMCaller(backend="mock", accuracy=1.0)  # 100% accurate
        for agent in agents:
            agent.llm_caller = llm

        # Create BFT
        bft = BFT4Agent(agents=agents, network=network)

        # Run consensus
        task = {"content": "2 + 2 = ?", "type": "math"}
        result = bft.run(task)

        assert result["success"] == True
        assert result["answer"] == "4"

        print(f"[OK] BFT consensus successful: answer={result['answer']}, time={result['total_time']:.2f}s")
        return True
    except Exception as e:
        print(f"[FAIL] Consensus test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("  BFT4Agent - Quick Test")
    print("=" * 60)

    tests = [
        test_imports,
        test_config,
        test_agents,
        test_network,
        test_consensus,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed! System is ready")
        print("\nNext step:")
        print("  Run demo: python main.py")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
