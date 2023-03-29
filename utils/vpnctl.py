#!/usr/bin/env python3
#TODO Refactor the script into a program.
#TODO Instead of generating random IP addresses using the socket and struct modules, use the ipaddress library.
#TODO Ensure that addresses are sorted so that the lowest addresses from the pool of available ones are allocated for new peers.
#TODO Add error handling to the _init_address_pool() method to raise a ValueError if the address space provided is invalid.
#TODO Add a method to allocate an IP address from the address pool to a peer, and handle the case where there are no available addresses left in the pool by raising a NoAvailableAddressesError.
#TODO Add a method to deallocate an IP address from a peer and return it to the address pool.
#TODO Add a method to find a peer by name and raise a PeerNotFoundError if the peer is not found.
#TODO Improve the __repr__ method for the Peer class to include only relevant attributes.
#TODO Add methods to the VPN class to create and delete peers.
#TODO Add a method to get a list of all peers in the VPN.
#TODO Add a method to get the number of available addresses in the address pool.
#TODO Add a method to get the number of allocated addresses in the address pool.
#TODO Improve the __repr__ method for the VPN class to include relevant information about the VPN, such as the name, address space, number of peers, and number of available addresses.

import ipaddress
import random
import socket
import struct
import base64
import subprocess

# Data types
from ipaddress import IPv4Network, IPv4Address
from typing import Optional, Union

# Exception handling classes
class NoAvailableAddressesError(Exception):
    pass

class PeerNotFoundError(Exception):
    pass

# Should be optional for testing purposes
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
    

# Cryptokey module
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class X25519:
    if HAS_CRYPTOGRAPHY:
        impl = "cryptography"
    else:
        impl = "wg"

    @staticmethod
    def genkey() -> str:
        if X25519.impl == "cryptography":
            private_key = X25519PrivateKey.generate()
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
            return base64.b64encode(private_key_bytes).decode()

        else:
            private_key = subprocess.check_output(["wg", "genkey"]).strip()
            return base64.b64encode(private_key).decode()

    @staticmethod
    def pubkey(privkey: str) -> str:
        if X25519.impl == "cryptography":
            private_key_bytes = base64.b64decode(privkey.encode())
            private_key = X25519PrivateKey.from_private_bytes(private_key_bytes)
            public_key_bytes = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            return base64.b64encode(public_key_bytes).decode()

        else:
            private_key_bytes = base64.b64decode(privkey.encode())
            public_key = subprocess.check_output(["wg", "pubkey"], input=private_key_bytes).strip()
            return base64.b64encode(public_key).decode()

    @staticmethod
    def genpsk() -> str:
        return X25519.genkey()

# End of Cryptokey module


# Client module
class User:
    def __init__(self, name: str = None):
        self.name = name or RandomGenerator.get_random_name()

    def __repr__(self) -> str:
        return f"User(name='{self.name}')"

class Device:
    def __init__(self, os=None):
        self.os = os or RandomGenerator.get_random_system()

class Peer(Device):
    def __init__(self, name=None, address=None, key=None, pub=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name or RandomGenerator.get_random_name()
        self.address = address or RandomGenerator.get_random_address()
        self.key = key if key is not None else X25519.genkey()
        self.pub = pub if pub is not None else X25519.pubkey(self.key)

    def __repr__(self) -> str:
        attrs = ['name', 'address', 'os', 'key', 'pub']
        return f"Peer({', '.join(f'{attr}={getattr(self, attr)!r}' for attr in attrs)})"
    
# End of Client module

# Server module
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
            raise NoAvailableAddressesError(
                f"Not enough addresses in pool. Only {self.number_of_available_addresses}"
                f"address{plural_suffix} {verb_suffix} available for allocation."
            )

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

# End of Server module

# Testing module
#TODO Implement unittesting instead all this mess...

from pprint import pprint

def test_user_creation(pretty_print=False):
    test_user = User()
    print("Printing user:")
    if pretty_print:
        pprint(test_user)
    else:
        print(test_user)
    print("Printing user's dictionary:")
    if pretty_print:
        pprint(test_user.__dict__)
    else:
        print(test_user.__dict__)

def test_device_creation(pretty_print=False):
    test_device = Device()
    print("Printing device:")
    if pretty_print:
        pprint(test_device)
    else:
        print(test_device)
    print("Printing device's dictionary:")
    if pretty_print:
        pprint(test_device.__dict__)
    else:
        print(test_device.__dict__)

def test_peer_creation(pretty_print=False):
    test_peer = Peer()
    print("Printing peer:")
    if pretty_print:
        pprint(test_peer)
    else:
        print(test_peer)
    print("Printing peer's dictionary:")
    if pretty_print:
        pprint(test_peer.__dict__)
    else:
        print(test_peer.__dict__)

def test_vpn_creation(pretty_print=False):
    test_vpn = VPN()
    print("Printing VPN:")
    if pretty_print:
        pprint(test_vpn)
    else:
        print(test_vpn)
    print("Printing VPN's dictionary:")
    if pretty_print:
        pprint(test_vpn.__dict__)
    else:
        print(test_vpn.__dict__)


def test_a_ton_of_stuff_at_once():
    
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

# End of Testing module

if __name__ == '__main__':
    test_user_creation(pretty_print=True)
    print()
    test_device_creation(pretty_print=True)
    print()
    test_peer_creation(pretty_print=True)
    print()
    test_vpn_creation(pretty_print=True)
    print()
    test_a_ton_of_stuff_at_once()
