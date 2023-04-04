# Champion's debug session setup

from pprint import pprint
import gc, inspect


# This funky stuff is gonna actualy provide
# the tools for address space dynamic distribution
# among the members of a very private net

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from typing import List, Optional, Union


@dataclass
class BasePeer:
    address: IPv4Address
    endpoint: Optional[IPv4Address] = None
    is_router: bool = False
    vpn: Optional[VPN] = None

    def __repr__(self) -> str:
        if self.is_router:
            return f"Router(address='{self.address}', endpoint='{self.endpoint}', vpn={self.vpn.pool.network.exploded})"
        else:
            return f"Peer(address='{self.address}', vpn={self.vpn.pool.network.exploded})"

    def __str__(self) -> str:
        if self.is_router:
            return f"Router: {self.address}"
        else:
            return f"Peer: {self.address}"


@dataclass
class Peer(BasePeer):
    pass


@dataclass
class Router(BasePeer):
    vpn: VPN

    @property
    def routes(self) -> List[IPv4Network]:
        return [self.vpn.pool.network]

    def __post_init__(self) -> None:
        self.is_router = True


@dataclass
class Pool:
    network: IPv4Network
    allocated_addresses: List[IPv4Address] = field(default_factory=list)

    def __post_init__(self):
        self.network = IPv4Network(self.network)

    def allocate_address(self, address: Optional[IPv4Address] = None) -> IPv4Address:
        if address is not None and address in self.allocated_addresses:
            raise ValueError(f"Error: Address {address} is already allocated.")

        # Loop through available addresses until an unallocated one is found
        for host in self.network.hosts().__iter__():
            if host not in self.allocated_addresses:
                self.allocated_addresses.append(host)
                return host

        # Raise an error if no unallocated addresses are available
        raise ValueError("Error: No available unallocated addresses in the pool.")

    def unallocate_address(self, address: IPv4Address) -> None:
        if address not in self.allocated_addresses:
            raise ValueError(f"Error: Address {address} is not allocated.")
        self.allocated_addresses.remove(address)

    @property
    def unallocated_addresses_left(self) -> int:
        return 2**(32-self.network.prefixlen) - 2 - len(self.allocated_addresses)


@dataclass
class VPN:
    pool: Pool
    peers: List[BasePeer] = field(default_factory=list)

    def __init__(self, network: Optional[Union[IPv4Network, str]] = None, endpoint: Optional[str] = None) -> None:
        if isinstance(network, str):
            network = IPv4Network(network)
        self.pool = Pool(network)
        self.peers = []
        if endpoint:
            self.add_peer(endpoint)

    def __repr__(self) -> str:
        return (
            f"VPN(network={self.pool.network}, endpoints={self.endpoints}, "
            f"left_in_pool={self.pool.unallocated_addresses_left}, peers={self.peers})"
        )

    @property
    def endpoints(self) -> List[str]:
        return [str(p.endpoint) for p in self.peers if isinstance(p, Router) and p.endpoint]

    def add_peer(self, address: Optional[Union[IPv4Address, str]] = None, endpoint: Optional[IPv4Address] = None) -> BasePeer:
        if isinstance(address, str):
            address = IPv4Address(address)
        address = self.pool.allocate_address(address)
        if endpoint is not None:
            router = Router(address, endpoint=endpoint, vpn=self)
            self.peers.append(router)
            return router
        else:
            peer = Peer(address, vpn=self)
            self.peers.append(peer)
            return peer

    def remove_peer(self, address: Optional[IPv4Address] = None) -> None:
        try:
            if address is None:
                peer = self.peers.pop()
                self.pool.unallocate_address(peer.address)
            else:
                peer = next(p for p in self.peers if p.address == address)
                self.peers.remove(peer)
                self.pool.unallocate_address(peer.address)
        except StopIteration:
            pass
