from __future__ import unicode_literals

from unittest import TestCase

# this exact order is required, we don't want the io one from Python 2
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from greptable import parse_config, print_servers


expected = """
sqlite:///:memory:
sqlite:///:memory::
MEM
MEM:
MEM::penguins
"""

config = """
[sqlite:///:memory:]
[sqlite://]
name = MEM
"""


class Test(TestCase):
    def setUp(self):
        self.servers = list(parse_config(config))

        cx = self.servers[1].engine.connect()
        cx.execute('CREATE TABLE penguins (name VARCHAR, type VARCHAR);')
        cx.close()

    def test_simple_output(self):
        testio = StringIO()
        print_servers(self.servers, testio)
        self.assertEqual(testio.getvalue().strip(), expected.strip())
