#!/usr/bin/env python3

import ipaddress
import random
import socket
import struct
import base64

# Data types
from ipaddress import IPv4Network, IPv4Address
from typing import Optional, Union

# Cryprographic methods
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

# Exception handling classes
class NoAvailableAddressesError(Exception):
    pass

class PeerNotFoundError(Exception):
    pass

# Optional for testing purposes
class RandomGenerator:
    NAMES = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Judy', 'Mallory', 'Oscar', 'Peggy', 'Quincy', 'Ralph', 'Sybil', 'Trent', 'Ursula', 'Victor', 'Wendy', 'Xavier', 'Yvonne', 'Zoe']
    SYSTEMS = ['Windows', 'MacOS', 'Linux', 'BolgenOS', 'Solaris']
    CITIES = ['Kiyv', 'New York', 'London', 'Paris', 'Tokyo', 'Beijing', 'Moscow', 'Berlin', 'Rome', 'Sydney', 'Rio de Janeiro', 'Cairo', 'Mumbai', 'Bangkok', 'Cape Town', 'Dubai', 'Toronto', 'Vancouver', 'Los Angeles', 'San Francisco', 'Chicago']
    
    @staticmethod
    def get_random_name() -> str:
        return random.choice(RandomGenerator.NAMES)

    @staticmethod
    def get_random_system() -> str:
        return random.choice(RandomGenerator.SYSTEMS)

    @staticmethod
    def get_random_city() -> str:
        return random.choice(RandomGenerator.CITIES)
    
    @staticmethod
    def get_random_address() -> str:
        #TODO Use `ipaddress` library instead
        return socket.inet_ntoa(struct.pack('>I', random.randint(0, 0xffffffff)))
    

class User:
    def __init__(self, name: str = None):
        self.name = name or RandomGenerator.get_random_name()

    def __repr__(self) -> str:
        return f"User(name='{self.name}')"


class WireGuard:
    @staticmethod
    def genkey() -> str:
        return base64.b64encode(
            X25519PrivateKey.generate().private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        ).decode()

    @staticmethod
    def pubkey(privkey: str) -> str:
        return base64.b64encode(
            X25519PrivateKey.from_private_bytes(base64.b64decode(privkey.encode()))
            .public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode()

    @staticmethod
    def genpsk() -> str:
        return WireGuard.genkey()


class Device:
    def __init__(self, os=None):
        self.os = os or RandomGenerator.get_random_system()

class Peer(Device):
    def __init__(self, name: str = None, address: IPv4Address = None, **kwargs):
        super().__init__(**kwargs)
        self.name = name or RandomGenerator.get_random_name()
        self.address = address or RandomGenerator.get_random_address()

    def __repr__(self) -> str:
        return f"Peer(name='{self.name}', address='{self.address}', os='{self.os}')"
    

class VPN:
    def __init__(self, name: str = None, address_space: Union[str, IPv4Network] = None, number_of_peers: int = 0):
        self.name = name or RandomGenerator.get_random_city()
        self.address_space = None
        self.address_pool = []
        self.peers = []
        self.number_of_available_addresses = 0
        self.number_of_peers = 0
        self._init_address_pool(address_space)
        if number_of_peers is not None:
            self.create_peers(number_of_peers)

    #TODO Ensure that addresses are sorted so that the lowest addresses from the pool of available ones are allocated for new peers
    def _init_address_pool(self, address_space: Union[str,IPv4Network]) -> None:
        if address_space is not None:
            try:
                self.address_space = ipaddress.ip_network(address_space)
                self.address_pool = list(self.address_space.hosts())
                self.number_of_available_addresses = len(self.address_pool)
            except ValueError:
                raise ValueError("Invalid address space.")

    def _create_peer(self, **kwargs) -> Peer:
        if not self.address_pool:
            raise NoAvailableAddressesError("No available addresses in address pool.")
        peer_address = self.address_pool.pop(0)
        self.number_of_available_addresses -= 1
        peer = Peer(address=peer_address, **kwargs)
        self.peers.append(peer)
        return peer

    def create_peer(self, **kwargs) -> Optional[Peer]:
        try:
            peer = self._create_peer(**kwargs)
        except NoAvailableAddressesError:
            return None
        return peer

    def create_peers(self, number_of_peers: int) -> None:
        if self.number_of_available_addresses < number_of_peers:
            plural_suffix = "es" if self.number_of_available_addresses != 1 else ""
            verb_suffix = "is" if self.number_of_available_addresses == 1 else "are"
            raise NoAvailableAddressesError(f"Not enough addresses in pool. Only {self.number_of_available_addresses} address{plural_suffix} {verb_suffix} available for allocation.")
        
        for _ in range(number_of_peers):
            self._create_peer()

    def delete_peer(self, identifier) -> bool:
        for peer in self.peers:
            if peer.name == identifier or peer.address == identifier or peer.os == identifier:
                self.peers.remove(peer)
                self.address_pool.append(peer.address)
                self.number_of_available_addresses += 1
                return True
        raise PeerNotFoundError(f"Peer with identifier {identifier} not found.")

    def __repr__(self) -> str:
        return f"VPN(name='{self.name}', address_space='{self.address_space}', number_of_peers='{self.number_of_peers}')"


#TODO Implement unittesting instead all this mess...
def test_user_creation():
    test_user = User()
    print("Printing user:", test_user)
    print("Printing user's dictionary:", test_user.__dict__)
test_user_creation()

def test_device_creation():
    test_device = Device()
    print("Printing device:", test_device)
    print("Printing device's dictionary:", test_device.__dict__)
test_device_creation()

def test_peer_creation():
    test_peer = Peer()
    print("Printing peer:", test_peer)
    print("Printing peer's dictionary:", test_peer.__dict__)
test_peer_creation()

def test_vpn_creation():
    test_vpn = VPN()
    print("Printing VPN:", test_vpn)
    print("Printing VPN's dictionary:", test_vpn.__dict__)
test_vpn_creation()


def test_a_ton_of_stuff_at_once():
    from pprint import pprint
    
    vpn0 = VPN(name='tokio', address_space=ipaddress.ip_network('10.0.0.0/28'), number_of_peers=8)

    print('Printing vpn0:\n',vpn0, '\n')
    print('Printing vpn0\'s dictionary:\n', vpn0.__dict__, '\n')

    print('Pretty printing the same:')
    pprint(vpn0.__dict__)
    print()

    vpn0.create_peer()

    print('Pretty printing the same after creating new peer:')
    pprint(vpn0.__dict__)
    print()

    vpn0.delete_peer(ipaddress.IPv4Address('10.0.0.1'))
    vpn0.create_peer()

    print('Doing the same as before but after deleting and creating one peer:')
    pprint(vpn0.__dict__)
    print()

test_a_ton_of_stuff_at_once()
