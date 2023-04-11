import unittest
from ipaddress import IPv4Network, IPv4Address
from configparser import ConfigParser
from io import StringIO
from vpn import VPN, Peer, Router, Pool

class TestVPN(unittest.TestCase):

    def setUp(self):
        self.vpn = VPN(network='192.168.0.0/24')

    def test_add_peer_without_endpoint(self):
        address = IPv4Address('192.168.0.2')
        peer = self.vpn.add_peer(address=address)
        self.assertIsInstance(peer, Peer)
        self.assertEqual(peer.address, address)
        self.assertIn(peer, self.vpn.peers)
        self.assertEqual(len(self.vpn.peers), 1)

    def test_add_peer_with_endpoint(self):
        address = IPv4Address('192.168.0.2')
        endpoint = IPv4Address('10.0.0.1')
        router = self.vpn.add_peer(address=address, endpoint=endpoint)
        self.assertIsInstance(router, Router)
        self.assertEqual(router.address, address)
        self.assertEqual(router.endpoint, endpoint)
        self.assertIn(router, self.vpn.peers)
        self.assertEqual(len(self.vpn.peers), 1)
        self.assertEqual(self.vpn.endpoints, [str(endpoint)])

    def test_remove_peer_with_address(self):
        address = IPv4Address('192.168.0.2')
        peer = self.vpn.add_peer(address=address)
        self.vpn.remove_peer(address=address)
        self.assertNotIn(peer, self.vpn.peers)
        self.assertEqual(len(self.vpn.peers), 0)

    def test_remove_peer_without_address(self):
        peer1 = self.vpn.add_peer(address='192.168.0.2')
        peer2 = self.vpn.add_peer(address='192.168.0.3')
        self.vpn.remove_peer()
        self.assertNotIn(peer2, self.vpn.peers)
        self.assertEqual(len(self.vpn.peers), 1)

    def test_to_json(self):
        address1 = IPv4Address('192.168.0.2')
        address2 = IPv4Address('192.168.0.3')
        endpoint = IPv4Address('10.0.0.1')
        router = self.vpn.add_peer(address=address1, endpoint=endpoint)
        peer = self.vpn.add_peer(address=address2)
        expected_json = (
            '{"network": "192.168.0.0/24", '
            '"peers": ['
            '{"type": "router", "address": "192.168.0.2", "endpoint": "10.0.0.1", "vpn_pool_network": "192.168.0.0/24"}, '
            '{"type": "peer", "address": "192.168.0.3"}]}'
        )
        self.assertEqual(self.vpn.to_json(), expected_json)

    def test_from_json(self):
        json_str = (
            '{"network": "192.168.0.0/24", '
            '"peers": ['
            '{"type": "router", "address": "192.168.0.2", "endpoint": "10.0.0.1", "vpn_pool_network": "192.168.0.0/24"}, '
            '{"type": "peer", "address": "192.168.0.3"}]}'
        )
        vpn = VPN.from_json(json_str)
        self.assertIsInstance(vpn, VPN)
        self.assertEqual(str(vpn.pool.network), '192.168
