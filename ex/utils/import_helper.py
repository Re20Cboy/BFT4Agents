"""
导入辅助模块
"""

import sys
import os
import importlib.util

def setup_bft4agent_imports():
    """设置bft4agent-simple模块导入"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../..'))
    bft4agent_path = os.path.join(project_root, 'bft4agent-simple')

    sys.path.insert(0, project_root)
    sys.path.insert(0, bft4agent_path)

    def import_module_from_path(module_name, file_path):
        if module_name in sys.modules:
            return sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    modules = {}
    module_files = {
        'bft4agent_simple.config': 'config.py',
        'bft4agent_simple.agents': 'agents.py',
        'bft4agent_simple.network': 'network.py',
        'bft4agent_simple.llm_new': 'llm_new.py',
        'bft4agent_simple.consensus': 'consensus.py',
        'bft4agent_simple.tasks': 'tasks.py',
    }

    for module_name, file_name in module_files.items():
        modules[module_name] = import_module_from_path(
            module_name,
            os.path.join(bft4agent_path, file_name)
        )

    return modules

# 自动设置导入
_bft4agent_modules = setup_bft4agent_imports()

# 导出
config = _bft4agent_modules['bft4agent_simple.config']
agents = _bft4agent_modules['bft4agent_simple.agents']
network = _bft4agent_modules['bft4agent_simple.network']
llm_new = _bft4agent_modules['bft4agent_simple.llm_new']
consensus = _bft4agent_modules['bft4agent_simple.consensus']
tasks = _bft4agent_modules['bft4agent_simple.tasks']

load_config = config.load_config
create_agents = agents.create_agents
Network = network.Network
LLMCaller = llm_new.LLMCaller
BFT4Agent = consensus.BFT4Agent
TaskLoader = tasks.TaskLoader
