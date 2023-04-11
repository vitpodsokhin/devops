# vpncls.py

from __future__ import annotations

import json

from dataclasses import dataclass, field
from typing import List, Optional, Union
from ipaddress import IPv4Address, IPv4Network

from io import StringIO
from configparser import ConfigParser

@dataclass
class BasePeer:
    address: IPv4Address
    endpoint: Optional[IPv4Address] = None
    is_router: bool = False
    vpn: Optional[VPN] = None

    def __repr__(self) -> str:
        if self.is_router:
            return f"Router(address='{self.address}', endpoint='{self.endpoint}', vpn={self.vpn})"
        elif self.vpn:
            return f"Peer(address='{self.address}')"
        else:
            return f"Peer(address='{self.address}', vpn={self.vpn})"

    def __str__(self) -> str:
        if self.is_router:
            return f"Router: {self.address}"
        else:
            return f"Peer: {self.address}"


@dataclass
class Peer(BasePeer):

    def __post_init__(self) -> None:
        self.is_router = False


@dataclass
class Router(BasePeer):
    vpn: VPN

    @property
    def routes(self) -> List[IPv4Network]:
        return [self.vpn.pool.network]

    def __post_init__(self) -> None:
        self.is_router = True


from ipaddress import IPv4Address, IPv4Network
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Pool:
    network: IPv4Network
    allocated_addresses: List[IPv4Address] = field(default_factory=list)

    def __post_init__(self):
        self.network = IPv4Network(self.network)

    def allocate_network(self, network: Optional[IPv4Network] = None) -> IPv4Network:
        # If no network is specified, allocate the whole network
        if network is None:
            self.allocated_addresses.append(self.network.network_address)
            return self.network

        # Find a suitable subnet
        for subnet in self.network.subnets():
            if subnet.prefixlen >= network.prefixlen and subnet not in self.allocated_addresses:
                self.allocated_addresses.append(subnet)
                return subnet

        # Raise an error if no suitable subnet is found
        raise ValueError("Error: No available unallocated subnets in the pool.")

    def allocate_address(self, address: Optional[IPv4Address] = None) -> IPv4Address:
        if address is not None and address in self.allocated_addresses:
            raise ValueError(f"Error: Address {address} is already allocated.")

        # if address is not None and address in self.network.:
        #     raise ValueError(f"Error: Address {address} is already allocated.")

        for host in iter(self.network.hosts()):
            if host not in self.allocated_addresses:
                self.allocated_addresses.append(host)
                return host

        raise ValueError("Error: No available unallocated addresses in the pool.")

    def unallocate_address(self, address: IPv4Address = None) -> None:
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

    def __init__(
            self, network: Optional[Union[IPv4Network, str]] = None,
            endpoint: Optional[str] = None
        ) -> None:
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

    def add_peer(
            self,
            address: Optional[Union[IPv4Address, str]] = None,
            endpoint: Optional[IPv4Address] = None
        ) -> BasePeer:
        '''Adds a new peer to the VPN.
        If an address is specified, it allocates that address from the VPN's pool.
        If an endpoint is specified, it creates a router peer with that endpoint.'''
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
        '''Removes a peer from the VPN.
        If an address is specified, it removes the peer with that address.
        Otherwise, it removes the last peer in the list.'''
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
        '''Prints the VPN configuration in INI file format.
        If a file_path is specified, it writes the configuration to that file instead.'''
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
            with open(file_path, 'w', encoding='utf-8') as f:
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


def main():

    #TODO implement the nessesary to handle and process the following user input:
    # > vpn = VPN('10.0.0.0/20', '1.1.1.1, 12.23.34.45:53, entpoint.to, endpoint.to:443', users=50)
    vpn = VPN('10.0.0.0/28', '1.1.1.1')
    vpn.add_peer(endpoint='12.23.34.45')

    # print('  ... Testing large allocations')
    for _ in range(4):
        vpn.add_peer()

    vpn_clone = VPN.from_json(vpn.to_json())
    print(vpn_clone.print_config())

if __name__ == '__main__':
    main()
