from __future__ import unicode_literals

from unittest import TestCase

# this exact order is required, we don't want the io one from Python 2
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from greptable import dump_servers, get_server, get_url, parse_config, MissingOpenURL, ServerNotFound


expected = """
sqlite:///:memory:
sqlite:///:memory::
MEM
MEM:
MEM::penguins
"""

config = """
[sqlite:///:memory:]
opentable = http://penguincorp/{schema}/{table}
[sqlite://]
name = MEM
opentable = http://{server.name}/t/{schema}/{table}
openschema = http://{server.name}/d/{schema}
"""


class Test(TestCase):
    def setUp(self):
        self.servers = list(parse_config(config))

        cx = self.servers[1].engine.connect()
        cx.execute('CREATE TABLE penguins (name VARCHAR, type VARCHAR);')
        cx.close()

    def test_parse_config(self):
        assert len(self.servers) == 2
        for server in self.servers:
            assert server.url.startswith('sqlite')

    def test_simple_output(self):
        testio = StringIO()
        dump_servers(self.servers, testio)
        self.assertEqual(testio.getvalue().strip(), expected.strip())

    def test_separators(self):
        testio = StringIO()
        dump_servers(self.servers, testio, '|')
        testio = testio.getvalue()
        assert '|' in testio
        for line in testio.splitlines():
            if ':memory:' not in line:
                assert ':' not in line

    def test_get_server(self):
        srv1 = get_server(self.servers, 'MEM')
        assert srv1.name == 'MEM'
        srv2 = get_server(self.servers, 'sqlite://')
        assert srv1 is srv2
        srv3 = get_server(self.servers, 'sqlite:///:memory:')
        assert srv3 is not srv2
        with self.assertRaises(ServerNotFound):
            get_server(self.servers, 'penguins')

    def test_geturl(self):
        with self.assertRaises(ServerNotFound):
            get_url(self.servers, 'pen:guin')
        with self.assertRaises(ValueError):
            get_url(self.servers, 'p:en:gu:in')
        with self.assertRaises(ValueError):
            get_url(self.servers, 'penguin')

        self.assertEqual(get_url(self.servers, 'MEM:a'), 'http://MEM/d/a')
        self.assertEqual(get_url(self.servers, 'MEM:a:b'), 'http://MEM/t/a/b')
        self.assertEqual(get_url(self.servers, 'sqlite:///:memory:|a', '|'), 'http://penguincorp/a/')
        self.assertEqual(get_url(self.servers, 'sqlite:///:memory:|a|b', '|'), 'http://penguincorp/a/b')

        with self.assertRaises(MissingOpenURL):
            get_url(parse_config("[p]\nname=p"), 'p:engu:in')
