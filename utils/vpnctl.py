#!/usr/bin/env python3

import random
import ipaddress
import uuid
from typing import Optional

class Peer:
    #TODO Move user manipulation mechanics to a separate class
    USER_NAMES = {
        'male': list('Adam Benjamin Cassidy Daniel Eric Frank George Henry Isaac John Kevin Liam Myron Nicholas Oliver Patrick Quentin Robert Sulik Thomas Ulysses Vik William Xavier Yosef Zachary'.split()),
        'female': list('Alice Beth Clair Dara Elena Fara Gera Helen Iona Jane Kate Lidya Maria Nino Olga Penelope Quinn Ruby Sophia Tessa Uma Victoria Willow Xandra Yara Zoe'.split(' '))
    }

    def __init__(self, name=None, address=None, endpoint=None) -> None:
        self._id = uuid.uuid4()
        self.name = name if name is not None else self._get_random_name()
        self.address = None
        if address is not None:
            try:
                self.address = ipaddress.ip_address(address)
            except ValueError:
                pass
        self.endpoint = endpoint

    def _get_random_name(self) -> str:
        name_type = random.choice(['male', 'female'])
        names = Peer.USER_NAMES[name_type]
        if not names:
            raise ValueError("No available names.")
        return names.pop(random.randrange(len(names)))

    def __repr__(self):
        if self.address is None:
            return f"Peer(name='{self.name}')"
        else:
            return f"Peer(name='{self.name}', address='{self.address}')"

class VPN:
    #TODO Ensure that addresses are sorted so that the lowest addresses from the pool of available ones are allocated for new peers
    def __init__(self, name=None, address_space=None, number_of_peers=None) -> None:
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

    def _create_peer(self, name=None, address=None) -> Peer:
        if not self.address_pool:
            print("No available addresses in address pool.")
            return None
        peer_address = self.address_pool.pop(0)
        self.number_of_available_addresses -= 1
        peer = Peer(name=name, address=peer_address)
        self.peers.append(peer)
        return peer

    def create_peer(self, name=None, endpoint=None) -> Optional[Peer]:
        peer = self._create_peer(name=name)
        if peer is None:
            return None
        if endpoint is not None:
            peer.endpoint = endpoint
        return peer

    def create_peers(self, number_of_peers) -> None:
        if self.number_of_available_addresses < number_of_peers:
            print(f'Not enough addresses in pool.\nOnly {self.number_of_available_addresses} addresses are available for allocation.')
            return
        for i in range(number_of_peers):
            self._create_peer()

    def delete_peer(self, identifier) -> bool:
        for peer in self.peers:
            if peer.name == identifier or peer.address == identifier or peer.endpoint == identifier:
                self.peers.remove(peer)
                self.address_pool.append(peer.address)
                self.number_of_available_addresses += 1
                return True
        print("Peer not found.")
        return False

    def __repr__(self):
        if self.address_space:
            return f"VPN(name='{self.name}', address_space='{self.address_space}')"
        else:
            return f"VPN(name='{self.name}')"


def test():
    from pprint import pprint
    
    vpn0 = VPN(name='tokio', address_space=ipaddress.ip_network('10.255.0.0/28'), number_of_peers=8)

    print('Printing vpn0:\n',vpn0, '\n')
    print('Printing vpn0\'s dictionary:\n', vpn0.__dict__, '\n')

    print('Pretty printing the same:')
    pprint(vpn0.__dict__)
    print()

    vpn0.create_peer()

    print('Pretty printing the same after creating new peer:')
    pprint(vpn0.__dict__)
    print()

    vpn0.delete_peer(ipaddress.IPv4Address('10.255.0.1'))
    vpn0.create_peer('Alice')

    print('Doing the same as before but after deleting and creating one peer:')
    pprint(vpn0.__dict__)
    print()

if __name__ == '__main__':
    test()