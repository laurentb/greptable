#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import argparse
import io
import os
import sys

from sqlalchemy import create_engine, inspect

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class NotEnoughParameters(ValueError):
    pass


class ServerNotFound(Exception):
    pass


class MissingOpenURL(Exception):
    pass


class Server(object):
    def __init__(self, url, name=None, openschema=None, opentable=None):
        if name is None:
            name = urlsplit(url).hostname
        if name is None:
            name = url
        self.url = url
        self.name = name
        self.openschema = openschema
        self.opentable = opentable
        self._engine = None

    @property
    def engine(self):
        if not self._engine:
            self._engine = create_engine(self.url)
        return self._engine

    def __str__(self):
        return self.name

    def schemas(self):
        inspector = inspect(self.engine)
        dbs = inspector.get_schema_names()
        if not len(dbs):
            yield Schema(self, inspector.default_schema_name)
        for dbname in dbs:
            yield Schema(self, dbname)

    def open_url(self, schema, table=None):
        opentable = self.opentable
        openschema = self.openschema or opentable
        if table:
            if not opentable:
                raise MissingOpenURL()
            return opentable.format(server=self, schema=schema, table=table)
        if not openschema:
            raise MissingOpenURL()
        return openschema.format(server=self, schema=schema, table='')


class Schema(object):
    def __init__(self, server, name):
        self.server = server
        self.name = name

    def tables(self):
        inspector = inspect(self.server.engine)
        for tablename in inspector.get_table_names(self.name):
            yield Table(self, tablename)

    def __str__(self, separator=':'):
        return '%s%s%s' % (self.server, separator, self.name or '')


class Table(object):
    def __init__(self, schema, name):
        self.schema = schema
        self.name = name

    def __str__(self, separator=':'):
        return '%s%s%s' % (self.schema.__str__(separator), separator, self.name)


def get_config(path):
    with io.open(path, encoding='utf-8') as f:
        config = f.read()
    return parse_config(config)


def parse_config(config_text):
    config = configparser.RawConfigParser()
    if hasattr(config, 'read_file'):
        config.read_file(io.StringIO(config_text))
    else:
        config.readfp(io.StringIO(config_text))
    for url in config.sections():
        items = dict(config.items(url))
        yield Server(url, items.get('name'), items.get('openschema'), items.get('opentable'))


def dump_servers(servers, outfile, separator=':'):
    for server in servers:
        print(server.__str__(), file=outfile)
        for schema in server.schemas():
            print(schema.__str__(separator), file=outfile)
            for table in schema.tables():
                print(table.__str__(separator), file=outfile)


def get_server(servers, name):
    for server in servers:
        if server.name == name:
            return server
    for server in servers:
        if server.url == name:
            return server
    raise ServerNotFound()


def get_url(servers, line, separator=':'):
    args = line.split(separator)
    server, schema, table = args + [None] * (3 - len(args))
    if schema or table:
        server = get_server(servers, server)
        return server.open_url(schema, table)
    raise NotEnoughParameters()


def main():
    def fp(filename):
        if filename == '-':
            return sys.stdout
        if os.path.exists(filename):
            raise argparse.ArgumentTypeError("File already exists.")
        return open(filename, 'w')

    def dump(args):
        servers = get_config(args.config)
        dump_servers(servers, args.output, args.separator)

    def opn(args):
        servers = get_config(args.config)
        try:
            url = get_url(servers, args.line, args.separator)
        except ServerNotFound:
            print("Could not find server in configuration", file=sys.stderr)
            return 2
        except MissingOpenURL:
            print("No open URL configured for this server", file=sys.stderr)
            return 3
        except ValueError:
            print("Invalid table or schema line", file=sys.stderr)
            return 4
        if args.show:
            print(url)
        else:
            print("Opening %s" % url, file=sys.stderr)
            sys.stderr.flush()
            os.execlp('xdg-open', 'xdg-open', url)

    # if user config exists, use it by default
    confpath = os.path.join(
        os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config')),
        'greptable.conf')
    if not os.path.exists(confpath):
        confpath = 'greptable.conf'

    parser = argparse.ArgumentParser(description="List tables of SQL databases for easy schema greps")
    parser.add_argument('-s', '--separator', default=':')
    parser.add_argument('-c', '--config', default=confpath)
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    dump_parser = subparsers.add_parser('dump', help="Dump the table list")
    dump_parser.add_argument('-o', '--output', default='-', type=fp)
    dump_parser.set_defaults(method=dump)

    dump_parser = subparsers.add_parser('open', help="Open a table or schema")
    dump_parser.add_argument('-s', '--show', action='store_true', help="only show the URL")
    dump_parser.add_argument('line', help="table or schema line to open")
    dump_parser.set_defaults(method=opn)

    args = parser.parse_args()
    sys.exit(args.method(args))


if __name__ == '__main__':
    main()
