import os
from asyncio import run, sleep, create_task, gather
import random
import networkx as nx
import matplotlib.pyplot as plt

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8


@dataclass(msg_id=1)
class MyMessage:
    clock: int  # We add an integer (technically a "long long") field "clock" to this message
    message = 'A message'


class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(MyMessage, self.on_message)
        self.lamport_clock = 0
        self.topology_graph = nx.Graph()

    def started(self) -> None:
        async def start_communication() -> None:
            if not self.lamport_clock:
                for p in self.get_peers():
                    self.ez_send(p, MyMessage(self.lamport_clock))
            else:
                self.cancel_pending_task("start_communication")
        
        # Register task to start communication periodically
        self.register_task("start_communication", start_communication, interval=5.0, delay=0)

    @lazy_wrapper(MyMessage)
    def on_message(self, peer: Peer, payload: MyMessage) -> None:
        # Update Lamport clock
        self.lamport_clock = max(self.lamport_clock, payload.clock) + 1
        print(self.my_peer, "current clock:", self.lamport_clock)
        # Synchronize with network
        self.ez_send(peer, MyMessage(self.lamport_clock))
        self.topology_graph.add_edge(str(self.my_peer.mid), str(peer.mid))

    def visualize_topology(self):
        # Visualize network topology using NetworkX and Matplotlib
        pos = nx.spring_layout(self.topology_graph)
        plt.figure(figsize=(10, 8))
        nx.draw(self.topology_graph, pos, with_labels=True, node_color='skyblue', node_size=800, edge_color='gray',
                font_size=10, font_color='black')
        plt.title("Network Topology")
        plt.show()

    def visualize_message_exchange(self):
        # Visualize message exchange
        plt.figure(figsize=(12, 8))
        for sender, receiver, timestamp in self.message_logs:
            plt.plot([sender, receiver], [timestamp, timestamp], marker='o')
        plt.xlabel('Peer')
        plt.ylabel('Timestamp')
        plt.title('Message Exchange')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    # def push_gossip(self):
    #     # Push-based gossip protocol
    #     async def push_gossip_task() -> None:
    #         for peer in self.get_peers():
    #             if random.random() < 0.5:  # Push to random subset of peers
    #                 self.ez_send(peer, MyMessage(self.lamport_clock))
    #         self.register_task("push_gossip", push_gossip_task, interval=10.0, delay=5.0)

    #     self.register_task("push_gossip", push_gossip_task, interval=10.0, delay=5.0)

    # def pull_gossip(self):
    #     # Pull-based gossip protocol
    #     async def pull_gossip_task() -> None:
    #         for peer in random.sample(self.get_peers(), k=min(5, len(self.get_peers()))):  # Pull from random subset
    #             self.ez_send(peer, MyMessage(self.lamport_clock))
    #         self.register_task("pull_gossip", pull_gossip_task, interval=15.0, delay=10.0)

    #     self.register_task("pull_gossip", pull_gossip_task, interval=15.0, delay=10.0)

    # def hybrid_gossip(self):
    #     # Hybrid gossip protocol combining push and pull
    #     async def hybrid_gossip_task() -> None:
    #         for peer in self.get_peers():
    #             if random.random() < 0.5:  # Push to random subset
    #                 self.ez_send(peer, MyMessage(self.lamport_clock))
    #             elif random.random() < 0.5:  # Pull from random subset
    #                 self.ez_send(peer, MyMessage(self.lamport_clock))
    #         self.register_task("hybrid_gossip", hybrid_gossip_task, interval=20.0, delay=15.0)

    #     self.register_task("hybrid_gossip", hybrid_gossip_task, interval=20.0, delay=15.0)


async def start_communities(num_nodes=100) -> None:
    tasks = []
    instances = []
    for i in range(num_nodes):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", f"ec{i}.pem")
        # Sparse topology: RandomWalk with fewer neighbors
        # Dense topology: RandomWalk with many neighbors or use other strategies
        builder.add_overlay("MyCommunity", "my peer",
                            [WalkerDefinition(Strategy.RandomWalk,
                                              20, {'timeout': 3.0})],
                            default_bootstrap_defs, {}, [('started',)])
        instance = IPv8(builder.finalize(), extra_communities={'MyCommunity': MyCommunity})
        instances.append(instance)
        task = create_task(instance.start())
        tasks.append(task)
        await sleep(0.1)  # Ensure staggered start

    await gather(*tasks)
    await sleep(60)

    # random.choice(instances).community_instance.push_gossip()
    # random.choice(instances).community_instance.pull_gossip()
    # random.choice(instances).community_instance.hybrid_gossip()
    random.choice(instances).community_instance.visualize_topology()
    # random.choice(instances).community_instance.visualize_message_exchange()

run(start_communities())
