from __future__ import annotations

# This funky stuff is gonna actualy provide
# the tools for address space dynamic distribution
# among the members of a very private net

import json

from io import StringIO
from configparser import ConfigParser
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
        elif self.vpn:
            return f"Peer(address='{self.address}')"
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
        '''Initializes a new VPN object.
        If a network is specified, it creates a pool with that network.
        If an endpoint is specified, it adds a peer with that endpoint.'''
        if isinstance(network, str):
            network = IPv4Network(network)
        self.pool = Pool(network)
        self.peers = []
        if endpoint:
            self.add_peer(endpoint=endpoint)

    def __repr__(self) -> str:
        '''Returns a string representation of the VPN object.'''
        return (
            f"VPN(network={self.pool.network}, endpoints={self.endpoints}, "
            f"left_in_pool={self.pool.unallocated_addresses_left}, peers={self.peers})"
        )

    @property
    def endpoints(self) -> List[str]:
        '''Returns a list of endpoint addresses for all the router peers in the VPN.'''
        return [str(p.endpoint) for p in self.peers if isinstance(p, Router) and p.endpoint]

    def add_peer(self, address: Optional[Union[IPv4Address, str]] = None, endpoint: Optional[IPv4Address] = None) -> BasePeer:
        '''Adds a new peer to the VPN. If an address is specified, it allocates that address from the VPN's pool. If an endpoint is specified, it creates a router peer with that endpoint.'''
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
        '''Removes a peer from the VPN. If an address is specified, it removes the peer with that address. Otherwise, it removes the last peer in the list.'''
        try:
            if address is None:
                peer = self.peers.pop()
                self.pool.unallocate_address(peer.address)
            else:
                if isinstance(address, str):
                    address = IPv4Address(address)
                    peer = next(p for p in self.peers if p.address == address)
                    self.peers.remove(peer)
                    self.pool.unallocate_address(peer.address)
        except StopIteration:
            pass

    def to_json(self) -> str:
        '''Returns a JSON string representation of the VPN object.'''
        data = {
            'network': str(self.pool.network),
            'peers': [],
        }
        for peer in self.peers:
            if isinstance(peer, Router):
                peer_data = {
                    'type': 'router',
                    'address': str(peer.address),
                    'endpoint': str(peer.endpoint),
                    'vpn_pool_network': str(peer.vpn.pool.network),
                }
            else:
                peer_data = {
                    'type': 'peer',
                    'address': str(peer.address),
                }
            data['peers'].append(peer_data)
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'VPN':
        '''Creates a new VPN object from a JSON string.'''
        data = json.loads(json_str)
        network = data.get('network')
        vpn = cls(network=network)
        for peer_data in data['peers']:
            if peer_data['type'] == 'router':
                address = IPv4Address(peer_data['address'])
                endpoint = IPv4Address(peer_data['endpoint'])
                vpn.add_peer(address=address, endpoint=endpoint)
            else:
                address = IPv4Address(peer_data['address'])
                vpn.add_peer(address=address)
        return vpn


    def print_config(self, file_path: Optional[str] = None) -> Optional[str]:
        '''Prints the VPN configuration in INI file format. If a file_path is specified, it writes the configuration to that file instead.'''
        config = ConfigParser()
        config.add_section('VPN')
        config.set('VPN', 'network', str(self.pool.network))
        for i, peer in enumerate(self.peers):
            section_name = f'Peer{i+1}'
            config.add_section(section_name)
            config.set(section_name, 'address', str(peer.address))
            if isinstance(peer, Router):
                config.set(section_name, 'endpoint', str(peer.endpoint))
        if file_path is not None:
            with open(file_path, 'w') as f:
                config.write(f)
        else:
            output = StringIO()
            config.write(output)
            return output.getvalue()

    @classmethod
    def from_config(cls, config_str: str) -> 'VPN':
        '''Creates a new VPN object from an INI file configuration string.'''
        config = ConfigParser()
        config.read_string(config_str)
        network = IPv4Network(config.get('VPN', 'network'))
        vpn = cls(network=network)
        for section_name in config.sections():
            if section_name != 'VPN':
                address = IPv4Address(config.get(section_name, 'address'))
                endpoint = config.get(section_name, 'endpoint', fallback=None)
                vpn.add_peer(address=address, endpoint=endpoint)
        return vpn


class VPNManager:
    def __init__(self) -> None:
        self.vpns = []

    def create_vpn(self, network: str, endpoint: Optional[str] = None) -> None:
        vpn = VPN(network=network, endpoint=endpoint)
        self.vpns.append(vpn)

    def delete_vpn(self, index: int) -> None:
        del self.vpns[index]

    def list_vpns(self) -> List[VPN]:
        return self.vpns

    def save_vpn_to_ini(self, vpn: VPN, file_path: str) -> None:
        config = ConfigParser()
        config.add_section('VPN')
        config.set('VPN', 'network', str(vpn.pool.network))
        for i, peer in enumerate(vpn.peers):
            section_name = f'Peer{i+1}'
            config.add_section(section_name)
            config.set(section_name, 'address', str(peer.address))
            if isinstance(peer, Router):
                config.set(section_name, 'endpoint', str(peer.endpoint))
        with open(file_path, 'w') as f:
            config.write(f)

    def load_vpn_from_ini(self, file_path: str) -> VPN:
        config = ConfigParser()
        config.read(file_path)
        network = config.get('VPN', 'network')
        vpn = VPN(network=network)
        for section_name in config.sections():
            if section_name != 'VPN':
                address = config.get(section_name, 'address')
                endpoint = config.get(section_name, 'endpoint', fallback=None)
                vpn.add_peer(address=address, endpoint=endpoint)
        self.vpns.append(vpn)

    def save_vpn_to_json(self, vpn: VPN, file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(vpn.to_dict(), f)

    def load_vpn_from_json(self, file_path: str) -> VPN:
        with open(file_path, 'r') as f:
            vpn_dict = json.load(f)
            vpn = VPN.from_dict(vpn_dict)
            self.vpns.append(vpn)
        return vpn


def main():

    vpn = VPN('10.0.0.0/28', '1.1.1.1')
    vpn.add_peer(endpoint='12.23.34.45')

    # print('  ... Testing large allocations')
    for _ in range(4):
        vpn.add_peer()

    vpn_clone = VPN.from_json(vpn.to_json())
    print(vpn_clone.to_json())

if __name__ == '__main__':
    main()
