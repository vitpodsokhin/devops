#!/usr/bin/env python3

import ipaddress
import uuid
from typing import Union, Optional
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network

class Endpoint:
    """
    Represents a network endpoint.
    """
    ...


class Peer:
    """
    Represents a peer in a VPN.

    Attributes:
        _id (uuid.UUID): A unique identifier for the peer.
        name (str): The name of the peer.
        address (ipaddress.IPv4Address or ipaddress.IPv6Address): The IP address of the peer.
        endpoint (Endpoint): The network endpoint of the peer.
    """
    def __init__(self, name: str = None, address: Union[str, IPv4Address, IPv6Address] = None, endpoint: Endpoint = None) -> None:
        """
        Initializes a new instance of the Peer class.

        Args:
            name (str, optional): The name of the peer.
            address (str or ipaddress.IPv4Address or ipaddress.IPv6Address, optional): The IP address of the peer.
            endpoint (Endpoint, optional): The network endpoint of the peer.
        """
        self._id = uuid.uuid4()
        self.name = name
        self.address = None
        if address is not None:
            try:
                self.address = ipaddress.ip_address(address)
            except ValueError:
                pass
        self.endpoint = endpoint

    def __repr__(self):
        if self.address is None:
            return f"Peer(name='{self.name}')"
        else:
            return f"Peer(name='{self.name}', address='{self.address}')"


class VPN:
    """
    Represents a Virtual Private Network.

    Attributes:
        _id (uuid.UUID): A unique identifier for the VPN.
        name (str): The name of the VPN.
        address_space (ipaddress.IPv4Network or ipaddress.IPv6Network): The IP address space used by the VPN.
        peers (List[Peer]): A list of peers connected to the VPN.
        address_pool (List[ipaddress.IPv4Address or ipaddress.IPv6Address]): A list of available IP addresses in the address space.
        number_of_available_addresses (int): The number of available IP addresses in the address pool.
    """

    def __init__(self, name: str = None, address_space: Union[str, IPv4Network, IPv6Network] = None, number_of_peers: int = None) -> None:
        """
        Initializes a new instance of the VPN class.

        Args:
            name (str, optional): The name of the VPN.
            address_space (str or ipaddress.IPv4Network or ipaddress.IPv6Network, optional): The IP address space used by the VPN.
            number_of_peers (int, optional): The number of peers to create for the VPN.
        """
        self._id = uuid.uuid4()
        self.name = name
        self.address_space = None
        self.peers = []
        self.address_pool = []
        self.number_of_available_addresses = 0

        if address_space is not None:
            try:
                self.address_space = ipaddress.ip_network(address_space)
                self.address_pool = list(self.address_space.hosts())
                self.number_of_available_addresses = len(self.address_pool)
            except ValueError:
                pass

        if number_of_peers is not None:
            self.create_peers(number_of_peers)

    def _create_peer(self, name: str = None, address: Union[str, IPv4Address, IPv6Address] = None) -> Peer:
        if not self.address_pool:
            print("No available addresses in address pool.")
            return None

        peer_address = self.address_pool.pop(0)
        self.number_of_available_addresses -= 1
        peer = Peer(name=name, address=peer_address)
        self.peers.append(peer)
        return peer

    def create_peer(self, name: str = None, endpoint: Endpoint = None) -> Optional[Peer]:
        peer = self._create_peer(name=name)
        if peer is None:
            return None
        if endpoint is not None:
            peer.endpoint = endpoint
        return peer

    def delete_peer(self, identifier: Union[str, IPv4Address, IPv6Address, Endpoint]) -> bool:
        for peer in self.peers:
            if peer.name == identifier or peer.address == identifier or peer.endpoint == identifier:
                self.peers.remove(peer)
                self.address_pool.append(peer.address)
                self.number_of_available_addresses += 1
                return True
        print("Peer not found.")
        return False

    def create_peers(self, number_of_peers: int) -> None:
        if self.number_of_available_addresses < number_of_peers:
            print(f'Not enough addresses in pool.\nOnly {self.number_of_available_addresses} addresses are available for allocation.')
            return

        for i in range(number_of_peers):
            self._create_peer(name=f'peer{i}')

    def __repr__(self):
        if self.address_space:
            return f"VPN(name='{self.name}', address_space='{self.address_space}')"
        else:
            return f"VPN(name='{self.name}')"


def main():
    from pprint import pprint
    vpn0 = VPN(name='tokio', address_space=ipaddress.ip_network('10.255.0.0/28'), number_of_peers=8)
    print('Printing vpn0:\n',vpn0)
    print('Printing vpn0\'s dictionary:\n', vpn0.__dict__)
    print('Pretty printing the same:')
    pprint(vpn0.__dict__)
    vpn0.create_peer()
    print('Pretty printing the same after creating new peer:')
    pprint(vpn0.__dict__)
    vpn0.delete_peer(ipaddress.IPv4Address('10.255.0.1'))
    vpn0.create_peer('Alice')
    print('Doing the same as before but after deleting and creating one peer:')
    pprint(vpn0.__dict__)


if __name__ == '__main__':
    main()