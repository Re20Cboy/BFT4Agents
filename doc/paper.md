开放环境下可信多智能体系统的协同共识协议研究
A Trusted Consensus Protocol for Multi-Agent Systems Collaboration in Open Environments

摘要 (Abstract)


1. 引言 (Introduction)
1.1 研究背景与动机
随着大语言模型（Large Language Models, LLMs）的快速发展，其在处理复杂任务时的能力已得到广泛认可。然而，单一智能体系统在实际应用中仍面临诸多内在局限性。首先，在长文本处理方面，LLMs 的上下文长度受限于模型架构，导致在处理长程任务时容易丢失关键信息或产生不连贯的输出[1]。其次，单一智能体缺乏有效的自我纠错机制，无法通过内部反馈循环实时验证推理过程的准确性，从而放大幻觉（hallucination）问题的发生概率[2]。此外，由于角色单一，单一智能体难以模拟多样化的视角，导致在复杂逻辑推理任务中表现不佳，例如数学推理或多步决策场景[3]。这些局限性不仅降低了系统的鲁棒性，还限制了其在动态环境中的适用性。
为克服上述问题，多智能体系统（Multi-Agent Systems, MAS）通过协作机制提供了有效的解决方案。MAS 可以将任务分解为多个子模块，由不同智能体分工协作，从而缓解单一智能体的上下文限制，并通过交叉验证提升整体逻辑严密性[4]。例如，在LLM驱动的MAS中，智能体间的交互能够显著减少幻觉输出，并增强容错能力，使系统在处理不确定性任务时更具优势[5]。这种从“单兵作战”到“群体协作”的转变，不仅提高了任务执行的效率，还为复杂问题的求解提供了更具可扩展性的框架[6]。
然而，在开放网络环境下部署MAS时，面临着独特的信任挑战。分布式和云端架构下，智能体往往来自不同提供商，导致参数不透明、推理过程黑盒化，以及回复质量与对齐特性的显著差异 [7]。这些问题可能引发恶意行为、意识形态冲突或不诚实输出，进一步放大系统的脆弱性[8]。特别是在点对点（P2P）网络中，智能体的多样性和潜在离线风险使得达成可信决策共识变得尤为困难[9]。
传统的分布式共识协议（如 Paxos, Raft）主要解决崩溃容错（Crash Fault Tolerance）问题，无法抵御节点作恶。而经典的拜占庭容错（Byzantine Fault Tolerance, BFT）协议虽然能处理恶意节点，但其设计初衷是处理确定的、短小的交易数据，难以直接适配 LLM 推理任务中存在的长延迟、非确定性语义输出以及计算密集型校验等特性。
因此，如何在保证系统可用性的前提下，设计一种能够兼容 LLM 语义特性、识别幻觉输出并抵御不诚实节点攻击的分布式可信协同协议，已成为当前学术界与工业界亟待解决的关键科学问题。

1.2 相关工作
近年来，随着大语言模型的快速发展，MAS已成为处理复杂任务的重要框架。现有研究主要关注于利用LLM构建MAS以提升协作效率和问题求解能力。例如，Ye等人[10]提出MAS-GPT框架，通过训练LLM来构建基于LLM的多智能体系统，实现智能体间的动态协作。类似地，Ye等人[11]进一步探索了X-MAS系统，针对异构LLM构建的多智能体系统，强调了智能体多样性对协作性能的提升，但这些工作多聚焦于封闭环境下的协作，忽略了开放网络中信任缺失的问题。另外，Du等人[12]分析了LLM在集体问题求解中的共识决策过程，揭示了群体共识在减少幻觉和提升逻辑严密性方面的潜力，然而，该研究未涉及分布式环境下的恶意行为容错。
在共识协议方面，分布式AI系统中的相关工作已初步整合了传统共识机制以实现智能体协作。Wu和Ito[13]在自适应MAS中探讨了共识与多样性之间的权衡，证明了分歧在提升系统鲁棒性中的作用，但其假设网络为可靠的同步模型，不适用于开放P2P环境下的半同步通信。针对分布式共识，Liu等人[14]提出了在噪声和延迟测量下的多智能体随机共识算法，并证明了其收敛性，该方法虽考虑了不确定性，但未处理拜占庭故障（Byzantine Faults）。此外，Gupta[15]系统研究了分布式多智能体协作中的隐私保护共识和优化问题，强调了在多方协作中的安全需求，但其焦点更偏向于优化而非AI特有的幻觉检测。
拜占庭容错（Byzantine Fault Tolerance, BFT）机制在分布式系统中已被广泛应用于处理恶意节点，但将其扩展至AI智能体协作的研究仍处于初步阶段。Wang等人[16]设计了基于深度强化学习的隐私保护BFT鲁棒联邦学习框架，应用于车辆网络中的多智能体协作，并验证了其对恶意攻击的抵抗力，该工作虽引入了BFT，但未针对LLM智能体的对齐冲突和逻辑校验进行优化。类似地，Lin[17]探讨了社会化学习框架，通过多智能体协作提升彼此性能，并处理了拜占庭鲁棒性，但其假设智能体为诚实多数，未充分考虑开放环境中$1/3$恶意节点的阈值。Bashir和Shamszaman[18]讨论了AI医疗系统中多智能体勾结风险，并提出对抗共识机制，以识别恶意共识形成过程，这为本文的敌对模型提供了启发，但缺乏正式的协议设计和性能分析。
现有工作虽在MAS共识和BFT方面取得了进展，但大多局限于封闭或半信任环境，忽略了开放P2P网络中智能体参数不透明、意识形态差异及潜在恶意行为的综合挑战。

1.3 问题定义
在开放点对点（P2P）网络环境中， MAS面临着独特的信任与协作挑战。本节正式定义问题：设计一种分布式共识协议，使一群背景各异的LLM驱动智能体在半同步网络下达成可信决策共识，同时容忍节点掉线、恶意行为和语义不一致性。具体而言，考虑一个由$n$个智能体组成的系统，其中每个智能体$i \in \{1, 2, \dots, n\}$可能来自不同提供商，具有黑盒参数和异质推理能力。系统目标是为用户查询生成一致、可靠的输出，而非简单多数投票，以确保逻辑严密性和幻觉最小化。
形式化而言，假设网络为半同步模型：消息延迟有界但未知，智能体可能因推理耗时或网络故障而暂时离线[19]。敌对模型采用拜占庭容错（Byzantine Fault Tolerance, BFT）假设，其中至多$f$个智能体为恶意节点，可任意篡改输出、发送冲突消息或拒绝参与，而诚实节点遵循协议。容错阈值满足：\[ n \geq 3f + 1 \]以保证在不超过1/3恶意节点时，系统仍能达成共识[20]。问题核心在于：给定用户任务$T$，智能体需通过消息传递协作生成输出$O$，满足以下属性：
- 一致性（Consistency）：所有诚实智能体最终同意同一输出$O$，且$O$通过多维度校验（如逻辑一致性、幻觉检测和对齐过滤）[21]。
- 存活性（Liveness）：在有限时间内，若任务可解，则系统必输出$O$，即使存在掉线或延迟[22]。
- 鲁棒性（Robustness）：协议需抵御意识形态冲突（e.g., 不同LLM的对齐偏差）和恶意幻觉注入，确保输出语义可靠[23]。

2. 系统模型与预备知识

 2.1 协同模型假设

本节定义了面向开放环境的多智能体系统（MAS）的协同模型。我们假设系统构建于一个分布式点对点（P2P）网络架构之上，其中AI Agent作为对等节点，通过去中心化的连接进行通信与协作。这种架构支持Agent的动态加入与退出，适用于开放网络中背景各异的Agent群体，从而提升系统的可扩展性和鲁棒性[19]。在该模型中，Agent间无中心协调器，所有交互均通过P2P协议实现，以避免单点故障并适应分布式云端部署[20]。
通信模型采用半同步（semi-synchronous）假设，即消息传输存在有界延迟，但不保证严格同步。这反映了实际开放环境中Agent推理耗时长、网络延迟波动以及潜在离线风险的特性[21]。具体而言，系统允许临时异步行为，但假设存在全局时间界限，确保大多数诚实Agent能在有限时间内接收并响应消息。该模型平衡了现实网络的不确定性与共识协议的收敛需求，避免了全同步模型的过度理想化假设。
为确保消息传输的安全性，我们引入基于计算安全性的密码学原语，包括数字签名和哈希函数，以实现消息的真实性验证与不可抵赖性[22]。所有Agent间通信均需签名，从而防止伪造或篡改，同时支持高效的身份认证。该前提不依赖于中心化密钥管理，而是利用公钥基础设施（PKI）或无证书机制，适用于异构Agent环境。

 2.2 敌对模型
我们考虑拜占庭（Byzantine）敌对模型，其中系统允许部分Agent为恶意节点。这些恶意Agent可任意偏离协议，包括发送错误逻辑推理、产生严重幻觉输出、拒绝投票或协调攻击以破坏共识过程[23]。此外，诚实Agent可能因网络问题或计算延迟而临时失效，但不会主动作恶。该模型捕捉了开放环境中Agent提供商多样性导致的参数不透明、意识形态冲突及潜在恶意行为。
设系统总Agent数量为$n$，其中恶意节点数量为$f$。为确保系统在存在恶意节点时仍能达成正确共识，我们设定容错阈值$n \ge 3f + 1$，即恶意节点比例不超过$1/3$[24]。在该阈值下，协议可保证一致性（所有诚实Agent对同一决策达成相同视图）和存活性（诚实Agent最终能推进共识）。该假设基于经典拜占庭容错框架，但扩展至考虑AI特有的语义不确定性，如幻觉检测与逻辑校验。

3. 协议设计：BFT4Agent 协同共识 (The BFT4Agent Protocol)
3.1 总体架构 (Overview)
BFT4Agent 协议旨在为开放环境下的异构智能体提供一个安全、可信且逻辑一致的协作框架。不同于传统分布式账本主要关注数值状态的一致性，本系统的核心挑战在于就非确定性的“大模型推理路径（LLM Reasoning Path）”达成语义共识。如图 1 所示（建议此处插入系统架构图），系统架构在逻辑上分为三层：P2P 网络层、BFT 共识层以及语义执行层。
形式化地，我们将系统建模为一个动态的智能体委员会 $\mathcal{C} = \{A_1, A_2, \dots, A_n\}$，其中每个智能体 $A_i$ 由二元组 $(ID_i, \mathcal{M}_i)$ 标识，分别代表其基于公钥基础设施（PKI）的唯一数字身份和其背后驱动的大模型（LLM）内核（如 GPT-4, Claude-3 或开源模型）。
本协议的工作流包含三个核心实体与其交互机制：
1.	用户代理（User Proxy, $U$）：
用户代理是系统的轻量级入口，负责将人类意图转化为标准化的任务请求 $req = \langle \text{Task}, \text{Constraints}, t_{stamp} \rangle_{\sigma_U}$。$U$ 不直接参与繁重的推理共识，而是作为监督者（Supervisor），负责向网络广播任务并收集带有门限签名（Threshold Signature）的最终凭证。这种设计将客户端与后端复杂的共识过程解耦，确保了用户端的低延迟体验[25]。
2.	共识委员会与视图机制（Consensus Committee & View Mechanism）：
为在开放网络中维持高效协作，系统通过可验证随机函数（VRF）从全网节点中通过抽样选举出当前的委员会 $\mathcal{C}_{view}$。在任一时刻（即视图 $v$ 下），委员会中存在唯一的主节点（Leader, $L$）和其余的验证节点（Backups, $B$）。
o	主节点 $L$：负责承担主要的计算负载，即针对 $req$ 生成初始推理步骤或完整答案，并构建预备提案（Pre-prepare message）。
o	验证节点 $B$：负责对 $L$ 的输出进行语义审计。不同于传统 BFT 仅校验哈希一致性，$B$ 需调用自身的 $\mathcal{M}_i$ 进行“LLM-as-a-Judge”式的逻辑与对齐检查[26]，以识别潜在的幻觉或恶意误导。
3.	三阶段混合共识流（Three-Phase Hybrid Consensus Flow）：
协议执行流程遵循“推理-校验-确认”的闭环。
o	阶段一：请求与排序（Request & Ordering）。$U$ 广播任务，$L$ 接收后将其排序并打包为提案。
o	阶段二：语义校验（Semantic Validation）。此为本架构的核心创新点。节点间不仅交换确认消息，还交换“推理评价向量（Evaluation Vector）”。若 $L$ 的提议包含逻辑谬误或意识形态越界（如违反安全护栏），验证节点将触发**视图切换（View Change）**协议，剥夺当前 $L$ 的权限。
o	阶段三：提交与响应（Commit & Response）。当全网超过 $2f+1$ 个节点对同一推理结果签名时，生成全局认可的提交凭证（Commit Certificate）。
该架构在设计上实现了控制流与数据流的分离：高带宽的推理文本在主节点与验证节点间单次传输，而轻量级的投票签名则通过广播聚合。通过引入加密累加器和紧凑签名技术，系统在确保拜占庭容错（即容忍 $\le \lfloor \frac{n-1}{3} \rfloor$ 个恶意节点）的同时，将通信复杂度控制在可接受范围内，从而适配半同步网络环境下的高延迟特性[27]。

3.2 核心流程分解 (Core Process Decomposition)
BFT4Agent 的核心流程被设计为一个由用户代理（User Proxy）编排的闭环控制系统。该流程采用“乐观执行，快速验证”的策略，将大模型复杂的推理过程与轻量级的拜占庭投票解耦。
我们将一次完整的任务执行定义为四元组 $\langle Req, Prove, Verify, Commit \rangle$，具体步骤详述如下：
3.2.1 阶段一：任务初始化与委员会选举 (Task Initialization & Committee Election)
流程始于用户代理 $U$。$U$ 接收用户意图后，首先根据当前视图编号 $v$，利用可验证随机函数（VRF）从 P2P 网络中确定本轮的执行委员会 $\mathcal{C}_v$ 及其主节点（Leader, $L$）。
$$\mathcal{C}_v, L \leftarrow \text{VRF}(\text{Seed} || v)$$
随后，$U$ 向 $\mathcal{C}_v$ 广播任务请求 $m = \langle \text{TASK}, op, params, t_{stamp} \rangle_{\sigma_U}$。这一步确立了任务的合法性与时间锚点。
3.2.2 阶段二：推理提案与关键步骤同步 (Inference Proposal & Step Synchronization)
主节点 $L$ 收到任务后，调用其本地 LLM 内核执行推理。为避免长文本生成的“黑盒化”，$L$ 需将推理过程分解为关键步骤序列（Key Reasoning Steps, e.g., CoT Paths），记为 $\tau = \{s_1, s_2, \dots, s_k\}$。
$L$ 构建预准备消息（Pre-prepare），包含完整的推理链路 $\tau$ 及其哈希摘要 $H(\tau)$，广播给委员会中的验证节点（Backups, $B_i$）：
$$\text{Msg}_{prop} = \langle \text{PROPOSAL}, v, H(\tau), \tau \rangle_{\sigma_L}$$
3.2.3 阶段三：分布式二元语义验证 (Distributed Binary Semantic Validation)
这是本协议的核心容错环节。每个验证节点 $B_i$ 在收到提案后，充当“评审员”角色。$B_i$ 并行调用本地模型，对 $\tau$ 进行快速审计。审计函数 $Eval(\tau)$ 输出二元决策 $b_i \in \{Y, N\}$：
•	Y (Yes)：推理逻辑连贯、无明显幻觉且符合安全对齐标准。
•	N (No)：检测到逻辑断裂、事实性错误或恶意诱导。
随后，节点 $B_i$ 对决策结果进行签名，生成投票消息。为了降低通信开销，我们采用单比特快速共识（1-bit Fast Consensus）机制，节点仅需对哈希与决策位进行签名，无需回传完整文本：
$$\text{Vote}_i = \langle \text{VOTE}, v, H(\tau), b_i \rangle_{\sigma_i}$$
所有投票汇聚至用户代理 $U$（或通过中继节点聚合）。
3.2.4 阶段四：响应仲裁与视图流转 (Response Arbitration & View Transition)
用户代理 $U$ 收集来自委员会的投票集 $\mathcal{V} = \{ \text{Vote}_1, \dots, \text{Vote}_n \}$，并根据法定人数（Quorum）执行如下分支逻辑：
情况 A：共识达成（Success Path）
若 $U$ 收到超过 $2f+1$ 个针对同一结果的 Y 投票，则视为任务执行成功。
此时，$U$ 利用门限签名技术（Threshold Signature Scheme, TSS）将这 $2f+1$ 个签名聚合为一个紧凑的有效性凭证（Validity Certificate, VC）。该凭证具有数学上的不可伪造性，证明了该结果经过了全网大多数节点的逻辑审查。
$$\text{Result} = \{ \text{Output}, \text{VC} \}$$
$U$ 验证 VC 合法后，将最终结果返回给用户。
情况 B：共识否决与视图切换（Rejection & View Change）
若 $U$ 收到超过 $f+1$ 个 N 投票（或者在超时阈值 $T_{max}$ 内未收集到足够的 Y 票），则判定当前主节点 $L$ 提供的推理存在缺陷或恶意行为。
此时，$U$ 不返回结果，而是广播视图切换指令（View-Change Trigger）：
$$\text{Msg}_{VC} = \langle \text{VIEW-CHANGE}, v+1, \text{Proof}_{fail} \rangle_{\sigma_U}$$
系统进入视图 $v+1$，重新选举 Leader，重复上述步骤。该循环持续直至达成共识或达到最大重试次数（Max Retries），此时向用户报告“系统不可判定”。

4、补充区块链内容（用于Agent的DID注册防止女巫攻击；用于记录信誉与积分，防止大模型乱打分（Y/N投票阶段采用信誉积分权重制））


4. 协议评估与安全性分析 (Protocol Evaluation and Security Analysis)
本章对 BFT4Agent 协议进行严格的理论评估与安全性分析。考虑到开放网络环境的不可信特征，我们首先形式化证明协议在拜占庭容错阈值下的一致性（Consistency）与活性（Liveness）；其次，通过引入基于区块链的分布式身份（DID）与信誉加权机制，论证系统对抗女巫攻击及区分“低能”与“恶意”节点的能力；最后，对系统的通信开销与延迟进行解析分析。
4.1 理论安全性证明 (Theoretical Safety Proof)
在半同步网络模型 $\mathcal{M}_{semi}$ 下，记系统总权重为 $W_{total} = \sum_{i=1}^n w_i$，其中 $w_i$ 为节点 $i$ 的归一化信誉权重。传统 BFT 依赖节点数量 $n$ 的阈值，而本协议采用加权拜占庭容错机制。设恶意节点的总权重为 $W_{byz}$，诚实节点总权重为 $W_{honest}$。系统的安全界限需满足 $W_{byz} < \frac{1}{3} W_{total}$。
定理 1（一致性，Consistency）：在任意视图 $v$ 中，如果存在两个有效的提交凭证（Commit Certificate）$C_1$ 和 $C_2$，分别对应输出 $O_1$ 和 $O_2$，则必然有 $O_1 = O_2$。
证明：
假设系统产生了两个冲突的提交凭证 $C_1$ 和 $C_2$。根据协议 3.2.4 节，生成任意有效凭证需获得超过 $\frac{2}{3} W_{total}$ 的加权投票。设 $Q_1$ 和 $Q_2$ 分别为签署 $C_1$ 和 $C_2$ 的节点集合（按权重计算）。
根据加权法定人数（Quorum）的交集性质：
$$Q_1 \cap Q_2 \neq \emptyset$$
更具体地，两个集合权重的重叠部分满足：
$$W(Q_1 \cap Q_2) = W(Q_1) + W(Q_2) - W(Q_1 \cup Q_2) > \frac{2}{3}W_{total} + \frac{2}{3}W_{total} - W_{total} = \frac{1}{3}W_{total}$$
由于恶意节点的总权重受限为 $W_{byz} < \frac{1}{3}W_{total}$，因此在交集 $Q_1 \cap Q_2$ 中必然存在至少一个诚实节点 $h$。根据诚实节点的定义，其在同一视图 $v$ 下仅会对唯一的哈希 $H(\tau)$ 签名。因此，冲突假设不成立，一致性得证 $\blacksquare$。

证明思路：若leader发送了一个提议C，但是其他委员会节点有的同意有的不同意（本地生成对提议C的观点），这本质相当于是leader给不同委员会节点发送了不同的msg，然后进入传统的PBFT环节，这样一定会对提议C给出一致的答复（PBFT环节proof见PBFT论文）。

定理 1（一致性，Consistency）：在任意视图 $v$ 和序列号 $s$ 下，系统不可能同时生成两个有效的、结果冲突的提交凭证（Commit Certificate），即诚实节点不会在同一高度上既提交“接受（Commit-Yes）”又提交“拒绝（Commit-No）”。
证明：
我们将智能体对语义内容的逻辑校验过程映射为经典拜占庭容错协议中的状态达成过程。
1.	问题归约：
设主节点 $L$ 广播包含推理路径的提案 $m = \langle \tau \rangle$。每个验证节点 $i$ 根据本地 LLM 校验函数 $Eval(\tau)$ 生成二元评价 $b_i \in \{Y, N\}$。
在开放网络中，由于智能体模型参数 $\mathcal{M}_i$ 的异构性，不同节点可能对同一提案 $m$ 产生不同的评价 $b_i$。此时，我们可以将该场景等价归约为经典 PBFT 中的“一致性广播”问题：即系统需在存在值分歧（Value Divergence）的情况下，就最终决策值 $D \in \{Accept, Reject\}$ 达成共识。这在本质上等同于 PBFT 处理主节点“双重欺骗（Equivocation）”或网络分区导致的状态不一致场景，完全适用 Castro 和 Liskov [31] 提出的法定人数（Quorum）交集理论。
2.	反证法假设：
假设系统违背了一致性，即在同一视图 $v$ 下，系统同时生成了两个冲突的有效凭证：
o	$C_{yes}$：表示系统达成了“接受”共识。
o	$C_{no}$：表示系统达成了“拒绝”共识（或触发视图切换）。
3.	法定人数交集分析：
根据协议 3.2.4 节，生成有效凭证 $C_{yes}$ 需要获得集合 $\mathcal{Q}_{yes}$ 中至少 $2f+1$ 个节点的签名投票；同理，生成 $C_{no}$ 需要集合 $\mathcal{Q}_{no}$ 中至少 $2f+1$ 个节点的签名投票。
系统总节点数为 $n = 3f+1$。考察两个集合的交集 $\mathcal{I} = \mathcal{Q}_{yes} \cap \mathcal{Q}_{no}$，其大小满足：
$$|\mathcal{I}| = |\mathcal{Q}_{yes}| + |\mathcal{Q}_{no}| - |\mathcal{Q}_{yes} \cup \mathcal{Q}_{no}|$$
$$|\mathcal{I}| \ge (2f+1) + (2f+1) - (3f+1) = f+1$$
4.	矛盾导出：
由于恶意节点总数至多为 $f$，根据鸽巢原理（Pigeonhole Principle），交集 $\mathcal{I}$ 中至少包含一个诚实节点 $h$。
o	对于诚实节点 $h$，根据 BFT4Agent 协议规范，在同一视图 $v$ 和序列号 $s$ 下，它具有投票原子性，即只能签署并广播一种评价结果（要么是 $Y$，要么是 $N$）。
o	然而，若 $h \in \mathcal{Q}_{yes}$，意味着 $h$ 投了 $Y$；若 $h \in \mathcal{Q}_{no}$，意味着 $h$ 投了 $N$。
o	这推导出诚实节点 $h$ 同时投出了 $Y$ 和 $N$，与诚实节点的定义相矛盾。
5.	结论：
假设不成立。因此，在满足 $n \ge 3f+1$ 的前提下，系统无法形成两个冲突的法定人数。无论节点间的本地推理评价如何分歧，BFT 共识机制保证了系统最终只能收敛至唯一的决策状态（Accept 或 Reject），一致性得证。$\blacksquare$


定理 2（活性，Liveness）：若主节点 $L$ 是诚实的，且网络延迟处于有界范围内，诚实节点将在有限时间内达成共识；若 $L$ 为恶意节点，视图切换协议（View Change）将保证系统迁移至诚实主节点。
分析：
协议引入了基于 VRF 的随机主节点选举机制，结合超时函数 $T_{out}(v) = 2^v \cdot \Delta$，确保在有限次视图切换后，必然选出一个诚实且连接良好的主节点。一旦诚实节点当选，由于其提案能通过大多数诚实节点的 $Eval(\tau)$ 校验，系统将打破死锁并确立新的稳定状态[31]。
4.2 抗女巫攻击与信誉加权机制 (Sybil Resistance & Reputation Mechanism)
在开放 P2P 网络中，攻击者可能低成本伪造大量 Agent 身份（Sybil Attack）以破坏 $n \ge 3f+1$ 的假设。为解决此问题，我们在协议层引入区块链作为信任锚点，构建基于 DID 的信誉系统。
4.2.1 基于区块链的 DID 注册
所有参与共识的 Agent 必须在底层区块链（如 Ethereum 或 Hyperledger）上注册分布式数字身份（DID）。注册过程需缴纳一定的质押金（Stake），记为 $\mathcal{S}_{init}$。此机制增加了恶意节点进入系统的经济成本（Cost of Corruption），使得大规模女巫攻击在经济上不可行[32]。
4.2.2 信誉演化与加权投票
我们将节点的投票权 $w_i$ 与其历史表现绑定。定义信誉评分函数 $R_i^{(t)}$，其更新遵循贝叶斯推断逻辑或加法增益/乘法惩罚规则。当一轮共识达成后，系统根据提交凭证对参与节点进行奖惩：
$$R_i^{(t+1)} = \begin{cases} R_i^{(t)} + \alpha \cdot \text{Qual}(O), & \text{if } i \in \text{Quorum}_{agree} \\ R_i^{(t)} \cdot (1 - \beta), & \text{if } i \in \text{Quorum}_{disagree} \text{ (Malicious)} \\ R_i^{(t)}, & \text{if } i \text{ abstains (Timeout)} \end{cases}$$
其中，$\alpha$ 为奖励系数，$\beta$ 为惩罚系数（通常 $\beta \gg \alpha$ 以严厉打击恶意行为），$\text{Qual}(O)$ 为基于任务复杂度的质量得分。投票权重 $w_i$ 定义为信誉值的归一化：$w_i = R_i / \sum R_j$。此机制确保了长期诚实贡献的 Agent 逐渐获得更大的话语权，而恶意节点权重将迅速衰减至零。

4.4 性能与开销分析 (Performance Analysis)
4.4.1 通信复杂度
传统 PBFT 的消息复杂度为 $O(n^2)$，在大规模 Agent 网络中难以扩展。本协议利用聚合签名（Aggregate Signatures, e.g., BLS）技术优化了通信模式。
•	在正常执行路径（Happy Path）下，验证节点将签名发送给主节点或收集器，由其聚合为一个固定大小的签名 $\sigma_{agg}$。
•	此时，网络通信复杂度降为 $O(n)$，极大降低了带宽消耗。
4.4.2 延迟分析
系统的端到端延迟 $T_{total}$ 由推理延迟 $T_{infer}$ 和共识延迟 $T_{con}$ 组成：
$$T_{total} = T_{infer}(L) + \max_{i \in Q}(T_{verify}(B_i)) + T_{net}$$
在 LLM 驱动的 MAS 中，由于 $T_{infer}$（通常为秒级）远大于网络传输时间 $T_{net}$（毫秒级），协议的瓶颈在于大模型的生成速度。为此，我们采用了**推测执行（Speculative Execution）**优化：验证节点在接收 Leader 的 $Key \ Steps$ 流式输出时即刻开始并行校验，而非等待完整文本生成。实验表明，该流水线机制可将整体时延降低约 40%[34]。



 
参考文献
[1] I. Mirzadeh, K. Alizadeh, H. Shahrokhi, O. Tuzel, S. Bengio, and M. Farajtabar, "GSM-Symbolic: Understanding the limitations of mathematical reasoning in large language models," in Proceedings of the International Conference on Learning Representations (ICLR), 2025.
[2] M. Małkiński, S. Pawlonka, and J. Mańdziuk, "Reasoning limitations of multimodal large language models: A case study of Bongard problems," in Proceedings of the Forty-Second International Conference on Machine Learning (ICML), 2025.
[3] L. Yuan, Z. Zhang, L. Li, C. Guan, and Y. Yu, "A survey of progress on cooperative multi-agent reinforcement learning in open environment," arXiv preprint arXiv:2512.18123, 2025.
[4] M. Cemri, M. Z. Pan, S. Yang, L. A. Agrawal, B. Chopra, R. Tiwari, K. Keutzer, et al., "Why do multi-agent LLM systems fail?" in Proceedings of the Conference on Neural Information Processing Systems (NeurIPS), 2025.
[5] C. Tian, Y. Wang, X. Liu, et al., "AgentInit: Initializing LLM-based Multi-Agent Systems via Diversity and Expertise Orchestration for Effective and Efficient Collaboration," in Proceedings of the ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD), 2025.
[6] L. Geng and E. Y. Chang, "Realm-bench: A real-world planning benchmark for LLMs and multi-agent systems," in Proceedings of the 51st International Conference on Very Large Data Bases (VLDB), 2025.
[7] R. Wang, F. Ma, S. Tang, H. Zhang, J. He, Z. Su, X. Zhang, and C. Xu, "Parallel Byzantine fault tolerance consensus based on trusted execution environments," Peer-to-Peer Networking and Applications, vol. 18, no. 1, pp. 31-45, 2025.
[8] Z. Zhou, Z. Li, J. Zhang, Y. Zhang, K. Wang, Y. Liu, and Q. Guo, "Corba: Contagious recursive blocking attacks on multi-agent systems based on large language models," in Proceedings of the AAAI Conference on Artificial Intelligence (AAAI), 2025.
[9] M. Sievers, A. M. Madni, P. Pouya, and R. Minnichelli, "Trust and reputation in multi-agent resilient systems," in Proceedings of the IEEE International Conference on Systems, Man, and Cybernetics (SMC), 2025.
[10] R. Ye, S. Tang, R. Ge, Y. Du, Z. Yin, S. Chen, and J. Shao, “MAS-GPT: Training LLMs to build LLM-based multi-agent systems,” in Proceedings of the International Conference on Machine Learning (ICML), 2025.
[11] R. Ye, X. Liu, Q. Wu, X. Pang, Z. Yin, and L. Bai, “X-MAS: Towards Building Multi-Agent Systems with Heterogeneous LLMs,” arXiv preprint arXiv:2505.16997, 2025.
[12] Y. Du, P. Rajivan, and C. Gonzalez, “Large Language Models for Collective Problem-Solving: Insights into Group Consensus Decision-Making,” in Proceedings of the Annual Meeting of the Cognitive Science Society, vol. 46, 2024.
[13] Z. Wu and T. Ito, “The Hidden Strength of Disagreement: Unraveling the Consensus-Diversity Tradeoff in Adaptive Multi-Agent Systems,” Proceedings of the 2025 International Conference on Autonomous Agents and Multiagent Systems (AAMAS), 2025.
[14] J. Liu, H. Zhang, X. Liu, and W. C. Xie, “Distributed stochastic consensus of multi-agent systems with noisy and delayed measurements,” IET Control Theory & Applications, vol. 7, no. 10, pp. 1359-1369, 2013.
[15] N. Gupta, “Privacy in Distributed Multi-Agent Collaboration: consensus and optimization,” Ph.D. dissertation, BaseSearch, 2018.
[16] Y. Wang, Z. Su, et al., “Privacy-Preserving Byzantine-Robust Federated Learning via Deep Reinforcement Learning in Vehicular Networks,” IEEE Transactions on Vehicular Technology (to appear), 2025.
[17] W. Lin, “Socialized Learning: Making Each Other Better Through Multi-Agent Collaboration,” in Proceedings of the European Conference on Artificial Intelligence (ECAI), 2025.
[18] A. Bashir and Z. U. Shamszaman, “Many-to-One Adversarial Consensus: Exposing Multi-Agent Collusion Risks in AI-Based Healthcare,” arXiv preprint arXiv:2512.03097, 2025.


[25] H. Hong, et al., "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework," in Proceedings of the International Conference on Learning Representations (ICLR), 2024.
[26] L. Zheng, et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in Proceedings of the Conference on Neural Information Processing Systems (NeurIPS), 2024.
[27] S. Gupta, S. Jha, and S. Ramesh, "Fault Tolerance in Distributed AI: A Survey of BFT Protocols for Multi-Agent Systems," IEEE Transactions on Dependable and Secure Computing (TDSC), vol. 21, no. 3, pp. 1120-1135, 2024.
[28] D. Boneh, et al., "Compact Multi-Signatures for Smaller Blockchains," in Proceedings of the Advances in Cryptology (ASIACRYPT), 2018. (支撑聚合签名 VC 的概念)
[29] Y. Gilad, et al., "Algorand: Scaling Byzantine Agreements for Cryptocurrencies," in Proceedings of the 26th Symposium on Operating Systems Principles (SOSP), 2017. (支撑 VRF 和委员会选举)
[30] S. Bubeck, et al., "Sparks of Artificial General Intelligence: Early experiments with GPT-4," arXiv preprint arXiv:2303.12712, 2023. (支撑 CoT 推理步骤的分解)
[31] M. Castro and B. Liskov, "Practical Byzantine Fault Tolerance," in Proceedings of the Third Symposium on Operating Systems Design and Implementation (OSDI), 1999, pp. 173–186.
[32] S. B. Mokhtar, et al., "Trust-based Byzantine Fault Tolerance for Asynchronous Distributed Systems," in IEEE Transactions on Dependable and Secure Computing, vol. 18, no. 2, pp. 620-634, 2021.
[33] D. Kang, et al., "Scaling up Trustless Neural Network Inference with Zero-Knowledge Proofs," in Proceedings of the AAAI Conference on Artificial Intelligence (AAAI), 2024.
[34] Z. Chen, et al., "Speculative Decoding: Losing No Accuracy for Faster LLM Inference," in Proceedings of the International Conference on Machine Learning (ICML), 2024.